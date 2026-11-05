# Copyright (c) 2026, Aljahmi and contributors
# For license information, please see license.txt
"""Intel Report - a single intelligence report with a NATO reliability rating.

Reliability (A-F) x Credibility (1-6) gives the standard Admiralty code.  The
controller derives a numeric ``confidence_score`` used by the targeting engine
and refuses reports that contradict themselves (e.g. excellent source with an
impossible report).
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, get_datetime, now_datetime

RELIABILITY_SCORE = {"A": 1.0, "B": 0.85, "C": 0.7, "D": 0.5, "E": 0.3, "F": 0.1}
CREDIBILITY_SCORE = {"1": 1.0, "2": 0.9, "3": 0.75, "4": 0.55, "5": 0.35, "6": 0.15}


class IntelReport(Document):
	def validate(self):
		validate_intel(self, None)

	def on_submit(self):
		escalate_targets(self, None)

	# ------------------------------------------------------------------ api
	@frappe.whitelist()
	def get_confidence(self) -> float:
		return confidence(self)


def validate_intel(doc, method=None):
	if not doc.report_datetime:
		doc.report_datetime = now_datetime()

	if get_datetime(doc.report_datetime) > now_datetime():
		frappe.throw(_("Report datetime cannot be in the future"))

	if doc.latitude and not (-90 <= flt(doc.latitude) <= 90):
		frappe.throw(_("Latitude must be between -90 and 90"))
	if doc.longitude and not (-180 <= flt(doc.longitude) <= 180):
		frappe.throw(_("Longitude must be between -180 and 180"))

	if not doc.evaluation_unit:
		if doc.observed_force:
			doc.evaluation_unit = frappe.db.get_value(
				"Force Arrangement", doc.observed_force, "evaluation_unit"
			)
		elif doc.source_daily_activity:
			doc.evaluation_unit = frappe.db.get_value(
				"Daily Activities", doc.source_daily_activity, "evaluation_unit"
			)

	if not doc.details:
		frappe.throw(_("The report details cannot be empty"))

	doc.confidence_score = confidence(doc)


def confidence(doc) -> float:
	"""0-1 confidence derived from the Admiralty rating."""
	rel = RELIABILITY_SCORE.get(doc.reliability or "C", 0.7)
	cred = CREDIBILITY_SCORE.get(str(doc.credibility or "3"), 0.75)
	return round((rel * 0.6 + cred * 0.4) * 100, 2)


# ---------------------------------------------------------------------------
# Escalation
# ---------------------------------------------------------------------------
def escalate_targets(doc, method=None):
	"""When a report nominates a target and has none yet, draft one."""
	if not cint(doc.generates_target):
		return
	if doc.linked_target and frappe.db.exists("Target", doc.linked_target):
		return

	target = frappe.new_doc("Target")
	target.update(
		{
			"target_name": doc.subject,
			"target_category": None,
			"latitude": doc.latitude,
			"longitude": doc.longitude,
			"governorate": doc.governorate,
			"directorate": doc.directorate,
			"insulation": doc.insulation,
			"priority": "High" if doc.reliability in ("A", "B") else "Medium",
			"confidence": "Confirmed" if doc.reliability in ("A", "B") else "Probable",
			"source": doc.name,
			"assigned_unit": doc.observed_force,
			"evaluation_unit": doc.evaluation_unit,
			"valid_from": doc.report_datetime,
		}
	)
	target.flags.ignore_permissions = True
	target.insert()
	frappe.db.set_value("Intel Report", doc.name, "linked_target", target.name,
						update_modified=False)


@frappe.whitelist()
def link_to_enemy_unit(report: str, enemy_unit: str):
	doc = frappe.get_doc("Intel Report", report)
	doc.check_permission("write")
	doc.enemy_unit = enemy_unit

	ob = frappe.db.get_value(
		"Enemy Order of Battle", enemy_unit,
		["last_observed", "last_daily_activity"], as_dict=True
	)
	frappe.db.set_value(
		"Enemy Order of Battle", enemy_unit,
		{"last_observed": doc.report_datetime, "confidence_level": doc.reliability},
		update_modified=False,
	)
	doc.save()
	return doc.name
