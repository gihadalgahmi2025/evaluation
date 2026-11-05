# Copyright (c) 2026, Aljahmi and contributors
# For license information, please see license.txt
"""Evaluation Criteria Group - a reusable bundle of criteria."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt

from evaluation.evaluation.mixins import MasterRecord


class EvaluationCriteriaGroup(MasterRecord):
	title_field = "group_name"

	def validate(self):
		super().validate()
		validate_group(self, None)


def validate_group(doc, method=None):
	if not doc.criteria_lines:
		frappe.throw(_("Add at least one criterion to the group"))

	seen = set()
	for row in doc.criteria_lines:
		if row.criterion in seen:
			frappe.throw(
				_("Criterion {0} is listed twice in this group").format(row.criterion),
				title=_("Duplicate criterion"),
			)
		seen.add(row.criterion)

		criterion_type = frappe.db.get_value("Evaluation Criteria", row.criterion, "applies_to")
		if criterion_type and criterion_type != doc.applies_to:
			frappe.throw(
				_("Row {0}: criterion {1} applies to {2}, not {3}").format(
					row.idx, row.criterion, criterion_type, doc.applies_to
				)
			)

	total = 0.0
	for row in doc.criteria_lines:
		criterion_weight = frappe.db.get_value("Evaluation Criteria", row.criterion, "weight")
		total += flt(row.weight_override) or flt(criterion_weight)
	if total <= 0:
		frappe.throw(_("The total weight of the group must be greater than zero"))


@frappe.whitelist()
def apply_group_to_card(group: str, score_card: str):
	"""Fill a score card's lines from a criteria group (idempotent)."""
	card = frappe.get_doc("Evaluation Score Card", score_card)
	card.check_permission("write")
	if card.docstatus != 0:
		frappe.throw(_("Only draft score cards can be rebuilt from a group"))

	group_doc = frappe.get_doc("Evaluation Criteria Group", group)
	if group_doc.applies_to != card.subject_type:
		frappe.throw(
			_("Group applies to {0} but the card evaluates {1}").format(
				group_doc.applies_to, card.subject_type
			)
		)

	card.set("criteria_group", group)
	card.set("score_lines", [])
	for line in group_doc.criteria_lines:
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
	card.save()
	return card.name
