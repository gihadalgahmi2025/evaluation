# Copyright (c) 2026, Aljahmi and contributors
# For license information, please see license.txt
"""Evaluation Criteria - the atomic unit of every score card."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt, cstr

from evaluation.evaluation.mixins import MasterRecord

VALID_TYPES = ("Numeric", "Boolean", "Percentage", "Formula")


class EvaluationCriteria(MasterRecord):
	title_field = "criterion_name"

	def validate(self):
		super().validate()
		validate_criteria(self, None)

	def on_update(self):
		invalidate_criteria_cache()


def validate_criteria(doc, method=None):
	"""Guard rails for a single criterion (also called from hooks)."""
	if doc.criterion_type not in VALID_TYPES:
		frappe.throw(_("Criterion Type must be one of {0}").format(", ".join(VALID_TYPES)))

	if flt(doc.weight) <= 0:
		frappe.throw(_("Weight must be greater than zero"))

	if flt(doc.weight) > 100:
		frappe.throw(_("Weight cannot exceed 100"))

	if doc.criterion_type in ("Percentage", "Numeric") and flt(doc.max_value) <= 0:
		frappe.throw(_("Max Value is required for {0} criteria").format(doc.criterion_type))

	if doc.criterion_type == "Formula" and not cstr(doc.formula_expression).strip():
		frappe.throw(_("Formula Expression is required for Formula criteria"))

	# A criterion name must be unique *per subject type*
	duplicate = frappe.db.exists(
		"Evaluation Criteria",
		{
			"criterion_name": doc.criterion_name,
			"applies_to": doc.applies_to,
			"name": ("!=", doc.name),
		},
	)
	if duplicate:
		frappe.throw(
			_("Criterion {0} already exists for {1}").format(doc.criterion_name, doc.applies_to)
		)


def invalidate_criteria_cache():
	frappe.cache.delete_keys("evaluation:criteria")


@frappe.whitelist()
def get_criteria_for(applies_to: str) -> list[dict]:
	"""Return the active criteria of a subject type, ordered for display."""
	return frappe.get_all(
		"Evaluation Criteria",
		filters={"applies_to": applies_to, "is_active": 1},
		fields=[
			"name", "criterion_name", "criterion_type", "weight",
			"max_value", "formula_expression", "description",
		],
		order_by="weight desc",
	)


@frappe.whitelist()
def test_expression(expression: str, value: float = 0, max_value: float = 100,
					weight: float = 1):
	"""Evaluate a formula criterion without saving it (used by the desk editor).

	Returns the normalised ratio (0-1) plus the intermediate values so the user
	can see exactly how their formula behaves.
	"""
	from evaluation.evaluation.doctype.evaluation_score_card.evaluation_score_card import (
		safe_eval,
	)

	if not (expression or "").strip():
		frappe.throw(_("Please provide an expression to test"))

	namespace = {
		"value": flt(value),
		"max_value": flt(max_value) or 100.0,
		"weight": flt(weight),
		"min": min,
		"max": max,
		"round": round,
		"abs": abs,
	}
	try:
		raw = safe_eval(expression, namespace)
	except Exception as exc:
		frappe.throw(_("Invalid expression: {0}").format(exc), title=_("Formula error"))

	ceiling = namespace["max_value"]
	return {
		"raw": round(flt(raw), 4),
		"ratio": round(max(0.0, min(1.0, flt(raw) / ceiling)) if ceiling else 0.0, 4),
		"weighted": round(flt(raw) / ceiling * namespace["weight"] if ceiling else 0.0, 4),
	}
