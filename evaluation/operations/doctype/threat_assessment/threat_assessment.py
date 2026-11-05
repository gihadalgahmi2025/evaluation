# Copyright (c) 2026, Aljahmi and contributors
# For license information, please see license.txt
"""Threat Assessment - capability x intent x opportunity per threat factor."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, getdate, nowdate

from evaluation.utils import THREAT_CUTOFFS, clamp

#: capability / intent / opportunity are scored 1-5
SCALE_MAX = 5


class ThreatAssessment(Document):
	def validate(self):
		compute_threat(self, None)

	@frappe.whitelist()
	def refresh(self):
		compute_threat(self, None)
		return self.overall_threat_level


def compute_threat(doc, method=None):
	if not doc.assessment_date:
		doc.assessment_date = nowdate()
	if getdate(doc.assessment_date) > getdate(nowdate()):
		frappe.throw(_("Assessment date cannot be in the future"))

	for row in doc.threat_lines:
		for field in ("capability", "intent", "opportunity"):
			value = cint(row.get(field))
			if value < 1 or value > SCALE_MAX:
				frappe.throw(
					_("Row {0}: {1} must be between 1 and {2}").format(
						row.idx, _(field.title()), SCALE_MAX
					)
				)
		row.threat_score = cint(round((row.capability * 0.5 + row.intent * 0.3
									   + row.opportunity * 0.2) / SCALE_MAX * 100))

	if not doc.threat_lines:
		doc.overall_threat_level = "Low"
		return

	average = sum(flt(r.threat_score) for r in doc.threat_lines) / len(doc.threat_lines)
	peak = max(flt(r.threat_score) for r in doc.threat_lines)
	combined = clamp(average * 0.7 + peak * 0.3, 0, 100) / 100.0

	for cutoff, label in THREAT_CUTOFFS:
		if combined >= cutoff:
			doc.overall_threat_level = label
			break


@frappe.whitelist()
def sector_threat_history(sector: str, limit: int = 12):
	return frappe.get_all(
		"Threat Assessment",
		filters={"sector": sector, "docstatus": ("<", 2)},
		fields=["name", "assessment_date", "overall_threat_level"],
		order_by="assessment_date desc",
		limit_page_length=cint(limit),
	)
