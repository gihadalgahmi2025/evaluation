# Copyright (c) 2026, Aljahmi and contributors
# For license information, please see license.txt
"""Evaluation Score Card - weighted scoring and unit ranking engine.

Scoring model
-------------
Each score line carries ``value`` (raw score) and ``criterion_weight``.
The weighted score of a line is::

    weighted_score = normalize(value, criterion) * criterion_weight

``normalize`` depends on the criterion type:

* **Numeric**    -> ``value / max_value`` capped at 1
* **Percentage** -> ``value / 100``
* **Boolean**    -> ``1`` when true else ``0``
* **Formula**    -> evaluated with a restricted namespace

The card's ``total_score`` is ``sum(weighted_score)`` over all lines,
normalised to a 0-100 scale by the sum of the weights used.
"""

from __future__ import annotations

import ast
import operator

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cstr, flt, getdate, nowdate

from evaluation.utils import clamp

#: whitelisted operators for formula criteria (no builtins, no imports)
_ALLOWED_BINOPS = {
	ast.Add: operator.add,
	ast.Sub: operator.sub,
	ast.Mult: operator.mul,
	ast.Div: operator.truediv,
	ast.Pow: operator.pow,
	ast.Mod: operator.mod,
}
_ALLOWED_UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}


class EvaluationScoreCard(Document):
	def validate(self):
		compute_total(self, None)
		validate_subject(self)
		self.status = self.status or "Draft"

	# ------------------------------------------------------------------ api
	@frappe.whitelist()
	def recalculate(self):
		"""Recompute the total from the current line values."""
		compute_total(self, None)
		self.db_set("total_score", self.total_score, update_modified=False)
		return self.total_score

	@frappe.whitelist()
	def freeze(self):
		"""Lock a reviewed card - no more edits allowed."""
		if self.status == "Approved":
			frappe.throw(_("This score card is already approved"))
		self.status = "Approved"
		self.save()


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def validate_subject(doc):
	"""Exactly one subject must be set, matching ``subject_type``."""
	field_map = {
		"Personality": "personality",
		"Army Chief": "army_chief",
		"Force Arrangement": "force_arrangement",
		"Evaluation Unit": None,
	}
	expected = field_map.get(doc.subject_type)
	if expected is None:
		return

	subject = doc.get(expected)
	if not subject:
		frappe.throw(
			_("Please select the {0} this score card evaluates").format(_(doc.subject_type))
		)

	# clear the other subject links so the record stays unambiguous
	for field in ("personality", "army_chief", "force_arrangement"):
		if field != expected and doc.get(field):
			doc.set(field, None)

	if doc.period_from and doc.period_to and getdate(doc.period_to) < getdate(doc.period_from):
		frappe.throw(_("Period To cannot be earlier than Period From"))


# ---------------------------------------------------------------------------
# Scoring engine
# ---------------------------------------------------------------------------
def compute_total(doc, method=None):
	"""Populate ``weighted_score`` per line and ``total_score`` on the card."""
	if not doc.score_lines:
		doc.total_score = 0.0
		return doc.total_score

	total_weight = 0.0
	total = 0.0
	error_lines: list[str] = []

	for line in doc.score_lines:
		criterion = frappe.get_cached_doc("Evaluation Criteria", line.criterion)
		weight = flt(line.criterion_weight) or flt(criterion.weight)
		line.criterion_weight = weight

		try:
			ratio = normalize_value(criterion, flt(line.value))
		except Exception as exc:  # noqa: BLE001 - report, never crash the save
			error_lines.append(f"#{line.idx} {criterion.criterion_name}: {exc}")
			ratio = 0.0

		line.weighted_score = round(ratio * weight, 4)
		total += line.weighted_score
		total_weight += weight

	doc.total_score = round(clamp(total / total_weight * 100 if total_weight else 0), 2)

	if error_lines:
		frappe.msgprint(
			_("Some criteria could not be evaluated:<br>{0}").format("<br>".join(error_lines)),
			title=_("Formula errors"),
			indicator="orange",
		)

	return doc.total_score


def normalize_value(criterion, value: float) -> float:
	"""Map a raw value to a 0-1 ratio for the given criterion."""
	ctype = criterion.criterion_type

	if ctype == "Boolean":
		return 1.0 if flt(value) else 0.0

	if ctype == "Percentage":
		return clamp(flt(value), 0, 100) / 100.0

	if ctype == "Numeric":
		max_value = flt(criterion.max_value) or 100.0
		return clamp(flt(value), 0, max_value) / max_value

	if ctype == "Formula":
		namespace = {
			"value": flt(value),
			"max_value": flt(criterion.max_value) or 100.0,
			"weight": flt(criterion.weight),
			"min": min,
			"max": max,
			"round": round,
			"abs": abs,
		}
		result = safe_eval(cstr(criterion.formula_expression), namespace)
		max_value = flt(criterion.max_value) or 100.0
		return clamp(flt(result), 0, max_value) / max_value

	return 0.0


def safe_eval(expression: str, namespace: dict) -> float:
	"""Evaluate a small arithmetic expression without ``eval``."""
	tree = ast.parse(expression, mode="eval")
	return _eval_node(tree.body, namespace)


def _eval_node(node, namespace):
	if isinstance(node, ast.Constant):
		if isinstance(node.value, (int, float)):
			return node.value
		raise ValueError(_("Only numbers are allowed in formulas"))

	if isinstance(node, ast.Name):
		if node.id in namespace:
			return namespace[node.id]
		raise ValueError(_("Unknown name {0} in formula").format(node.id))

	if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BINOPS:
		return _ALLOWED_BINOPS[type(node.op)](
			_eval_node(node.left, namespace), _eval_node(node.right, namespace)
		)

	if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARY:
		return _ALLOWED_UNARY[type(node.op)](_eval_node(node.operand, namespace))

	if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
		fn = namespace.get(node.func.id)
		if callable(fn):
			return fn(*[_eval_node(a, namespace) for a in node.args])

	raise ValueError(_("Unsupported expression in formula"))


# ---------------------------------------------------------------------------
# Ranking
# ---------------------------------------------------------------------------
def refresh_ranking(doc, method=None):
	"""Assign a dense rank inside (subject_type, period) after every save."""
	if doc.docstatus == 2:
		return

	rows = frappe.db.sql(
		"""
		SELECT name, total_score
		FROM `tabEvaluation Score Card`
		WHERE subject_type = %s
		  AND IFNULL(period_from, '1000-01-01') = IFNULL(%s, '1000-01-01')
		  AND IFNULL(period_to, '9999-12-31') = IFNULL(%s, '9999-12-31')
		  AND evaluation_unit = %s
		  AND docstatus < 2
		ORDER BY total_score DESC, modified ASC
		""",
		(doc.subject_type, doc.period_from, doc.period_to, doc.evaluation_unit),
		as_dict=True,
	)

	rank = 0
	previous = None
	for index, row in enumerate(rows, start=1):
		if previous is None or flt(row.total_score) < flt(previous):
			rank = index
			previous = row.total_score
		if row.name == doc.name:
			if flt(doc.rank) != rank:
				frappe.db.set_value("Evaluation Score Card", doc.name, "rank", rank,
									update_modified=False)
			return


@frappe.whitelist()
def build_score_card(subject_type: str, subject: str, criteria_group: str,
					 evaluation_unit: str, period_from: str | None = None,
					 period_to: str | None = None) -> str:
	"""Create a draft score card pre-filled from a criteria group."""
	if not frappe.db.exists("Evaluation Criteria Group", criteria_group):
		frappe.throw(_("Criteria Group {0} does not exist").format(criteria_group))

	card = frappe.new_doc("Evaluation Score Card")
	card.update(
		{
			"score_card_title": f"{subject} - {nowdate()}",
			"evaluation_unit": evaluation_unit,
			"subject_type": subject_type,
			"criteria_group": criteria_group,
			"status": "Draft",
			"period_from": period_from or nowdate(),
			"period_to": period_to or nowdate(),
		}
	)
	field = {
		"Personality": "personality",
		"Army Chief": "army_chief",
		"Force Arrangement": "force_arrangement",
	}.get(subject_type)
	if field:
		card.set(field, subject)

	group = frappe.get_doc("Evaluation Criteria Group", criteria_group)
	if group.applies_to != subject_type:
		frappe.throw(
			_("Group {0} applies to {1}, not {2}").format(
				criteria_group, group.applies_to, subject_type
			)
		)

	for line in group.criteria_lines:
		criterion = frappe.get_cached_doc("Evaluation Criteria", line.criterion)
		card.append(
			"score_lines",
			{
				"criterion": criterion.name,
				"criterion_weight": flt(line.weight_override) or criterion.weight,
				"value": 0,
				"weighted_score": 0,
			},
		)

	card.flags.ignore_permissions = True
	card.insert()
	return card.name
