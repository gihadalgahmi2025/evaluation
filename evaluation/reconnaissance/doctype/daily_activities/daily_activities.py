# Copyright (c) 2026, Aljahmi and contributors
# For license information, please see license.txt
"""Daily Activities - one row per field observation.

This is the busiest transactional DocType of the app.  It turns a raw
observation into downstream effects:

* updates the observed unit's ``last_daily_activity`` / posture / strength
* optionally raises an **Intel Report** (``generates_intel``)
* optionally nominates a **Target** (``generates_target``)
* writes readiness and spread deltas as child rows for trend analysis

Everything is idempotent: re-submitting the same document never duplicates the
downstream records (the link is stored back on the activity).
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, cstr, flt, getdate, now_datetime, nowdate

from evaluation.utils import CONFIDENCE_LEVELS


class DailyActivities(Document):
	def validate(self):
		validate_activity(self, None)

	def before_submit(self):
		self.flags.ignore_mandatory = False

	def on_submit(self):
		after_submit_activity(self, None)

	def on_cancel(self):
		on_cancel_activity(self, None)

	# ------------------------------------------------------------------ api
	@frappe.whitelist()
	def create_intel_report(self) -> str:
		"""Raise (or return the existing) intel report for this observation."""
		if self.auto_intel_report and frappe.db.exists("Intel Report", self.auto_intel_report):
			return self.auto_intel_report
		return _make_intel_report(self)

	@frappe.whitelist()
	def nominate_target(self) -> str:
		"""Create a draft target from this observation."""
		return _make_target(self)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def validate_activity(doc, method=None):
	if not doc.start_of_event:
		doc.start_of_event = nowdate()

	if getdate(doc.start_of_event) > getdate(nowdate()):
		frappe.throw(_("Observation date cannot be in the future"))

	if not doc.date:
		doc.date = now_datetime()

	if not doc.creator_of_the_report:
		doc.creator_of_the_report = frappe.session.user

	# weekday shortcut used by the list view filters
	if doc.start_of_event:
		doc.today = getdate(doc.start_of_event).strftime("%A")

	# one observation per (unit, day, topic) keeps the timeline clean
	duplicate = frappe.db.exists(
		"Daily Activities",
		{
			"military_division": doc.military_division,
			"start_of_event": doc.start_of_event,
			"the_topic": doc.the_topic,
			"name": ("!=", doc.name),
			"docstatus": ("<", 2),
		},
	)
	if duplicate:
		frappe.throw(
			_("An observation for {0} on {1} with the same topic already exists: {2}").format(
				doc.military_division, doc.start_of_event, duplicate
			),
			title=_("Duplicate observation"),
		)

	# inherit posture / geography from the observed unit when left blank
	if doc.military_division:
		unit = frappe.db.get_value(
			"Force Arrangement",
			doc.military_division,
			["current_posture", "governorate_name", "directorate_name", "insulation", "evaluation_unit"],
			as_dict=True,
		)
		if unit:
			doc.inferred_posture = unit.current_posture
			doc.governorate_name = doc.governorate_name or unit.governorate_name
			doc.directorate_name = doc.directorate_name or unit.directorate_name
			doc.insulation = doc.insulation or unit.insulation
			if not doc.evaluation_unit and unit.evaluation_unit:
				doc.evaluation_unit = unit.evaluation_unit

	# derived strength data from readiness deltas
	if doc.readiness_changes:
		total_adjustment = sum(flt(r.adjustment) for r in doc.readiness_changes)
		if total_adjustment:
			doc.augmentation_and_reduction_div = (
				"Enhanced" if total_adjustment > 0 else "Reduced"
			)


# ---------------------------------------------------------------------------
# Submit / cancel side effects
# ---------------------------------------------------------------------------
def after_submit_activity(doc, method=None):
	"""Fan-out: update the unit, raise intel / targets."""
	update_observed_unit(doc)

	if cint(doc.generates_intel):
		report = doc.auto_intel_report
		if not report or not frappe.db.exists("Intel Report", report):
			report = _make_intel_report(doc)
			frappe.db.set_value("Daily Activities", doc.name, "auto_intel_report", report,
								update_modified=False)

	if cint(doc.generates_target):
		_make_target(doc, silent=True)


def update_observed_unit(doc):
	if not doc.military_division:
		return

	values = {"last_daily_activity": doc.name, "last_observed": doc.date or now_datetime()}
	if doc.inferred_posture:
		values["current_posture"] = doc.inferred_posture

	change = doc.augmentation_and_reduction_div
	if change in ("Enhanced", "Reduced"):
		current = flt(
			frappe.db.get_value("Force Arrangement", doc.military_division, "strength_pct") or 100
		)
		delta = flt(
			sum(flt(r.adjustment) for r in doc.readiness_changes)
		) if doc.readiness_changes else 5.0
		new_strength = max(0.0, min(100.0, current + (delta if change == "Enhanced" else -abs(delta))))
		values["strength_pct"] = round(new_strength, 2)

	frappe.db.set_value("Force Arrangement", doc.military_division, values,
						update_modified=False)


def on_cancel_activity(doc, method=None):
	"""Reverse the link on the observed unit so no stale pointers remain."""
	if doc.military_division:
		unit = frappe.db.get_value(
			"Force Arrangement", doc.military_division, "last_daily_activity"
		)
		if unit == doc.name:
			frappe.db.set_value(
				"Force Arrangement", doc.military_division,
				{"last_daily_activity": None},
				update_modified=False,
			)


# ---------------------------------------------------------------------------
# Downstream document creation
# ---------------------------------------------------------------------------
def _make_intel_report(doc) -> str:
	report = frappe.new_doc("Intel Report")
	report.update(
		{
			"report_datetime": doc.date or now_datetime(),
			"source_type": "Field Recon",
			"reliability": "B",
			"credibility": "3",
			"subject": doc.the_topic,
			"enemy_unit": None,
			"observed_force": doc.military_division,
			"latitude": doc.spread_map and frappe.db.get_value(
				"Geolocation", doc.spread_map, "latitude"
			) or None,
			"longitude": doc.spread_map and frappe.db.get_value(
				"Geolocation", doc.spread_map, "longitude"
			) or None,
			"governorate": doc.governorate_name,
			"directorate": doc.directorate_name,
			"insulation": doc.insulation,
			"details": doc.text_summary or doc.notes,
			"source_daily_activity": doc.name,
			"evaluation_unit": doc.evaluation_unit,
			"generates_target": cint(doc.generates_target),
		}
	)
	report.flags.ignore_permissions = True
	if doc.linked_target:
		report.linked_target = doc.linked_target
	report.insert()
	return report.name


def _make_target(doc, silent: bool = False) -> str:
	if doc.linked_target and frappe.db.exists("Target", doc.linked_target):
		return doc.linked_target

	target = frappe.new_doc("Target")
	target.update(
		{
			"target_name": doc.the_topic,
			"governorate": doc.governorate_name,
			"directorate": doc.directorate_name,
			"insulation": doc.insulation,
			"assigned_unit": doc.military_division,
			"priority": "Medium",
			"confidence": "Probable",
			"evaluation_unit": doc.evaluation_unit,
			"source": doc.auto_intel_report,
			"valid_from": doc.date,
		}
	)
	target.flags.ignore_permissions = True
	target.insert()
	frappe.db.set_value("Daily Activities", doc.name, "linked_target", target.name,
						update_modified=False)
	if not silent:
		frappe.msgprint(
			_("Draft target {0} created").format(
				f'<a href="/app/target/{target.name}">{target.name}</a>'
			),
			alert=True,
		)
	return target.name


# ---------------------------------------------------------------------------
# Scheduled / bulk helpers
# ---------------------------------------------------------------------------
def flag_missing_observations(days: int = 3):
	"""Notify when a high priority unit had no observation for ``days`` days."""
	rows = frappe.db.sql(
		"""
		SELECT name, name_div, last_observed
		FROM `tabForce Arrangement`
		WHERE is_group = 0
		  AND IFNULL(last_observed, '2000-01-01') < DATE_SUB(NOW(), INTERVAL %s DAY)
		""",
		(days,),
		as_dict=True,
	)
	for row in rows:
		frappe.publish_realtime(
			"eval:observation_stale",
			{"unit": row.name, "unit_name": row.name_div, "last_observed": row.last_observed},
		)
	return rows
