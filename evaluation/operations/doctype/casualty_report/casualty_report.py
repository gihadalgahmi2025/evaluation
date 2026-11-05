# Copyright (c) 2026, Aljahmi and contributors
# For license information, please see license.txt
"""Casualty Report - enemy losses and how they change combat power."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, get_datetime, now_datetime

from evaluation.utils import clamp


class CasualtyReport(Document):
	def validate(self):
		compute_casualties(self, None)

	def on_submit(self):
		apply_strength_change(self, None)

	@frappe.whitelist()
	def recalculate(self):
		compute_casualties(self, None)
		return {"kia": self.total_kia, "wia": self.total_wia, "after": self.strength_pct_after}


def compute_casualties(doc, method=None):
	if not doc.report_datetime:
		doc.report_datetime = now_datetime()
	if get_datetime(doc.report_datetime) > now_datetime():
		frappe.throw(_("Report datetime cannot be in the future"))

	doc.total_kia = sum(
		cint(r.count) for r in doc.personnel_lines if (r.casualty_type or "") == "KIA"
	)
	doc.total_wia = sum(
		cint(r.count) for r in doc.personnel_lines if (r.casualty_type or "") == "WIA"
	)

	# estimate the strength after the losses
	base_strength = 100.0
	if doc.force_arrangement:
		base_strength = flt(
			frappe.db.get_value("Force Arrangement", doc.force_arrangement, "strength_pct") or 100
		)
		# the head-count estimate lives on the linked Enemy Order of Battle node
		ob_strength = None
		linked_ob = frappe.db.get_value(
			"Force Arrangement", doc.force_arrangement, "linked_enemy_ob"
		)
		if linked_ob:
			ob_strength = flt(
				frappe.db.get_value("Enemy Order of Battle", linked_ob, "estimated_strength")
				or 0
			) or None

	losses = doc.total_kia + doc.total_wia * 0.5
	if ob_strength:
		doc.strength_pct_after = round(
			clamp(base_strength - (losses * 100.0 / ob_strength)), 2
		)
	else:
		doc.strength_pct_after = round(clamp(base_strength - losses), 2)

	for row in doc.personnel_lines:
		if cint(row.count) < 0:
			frappe.throw(_("Row {0}: casualty count cannot be negative").format(row.idx))
	for row in doc.equipment_lines:
		if flt(row.quantity_lost) < 0:
			frappe.throw(_("Row {0}: quantity lost cannot be negative").format(row.idx))


def apply_strength_change(doc, method=None):
	"""Persist the new strength on the observed unit after submit."""
	if not doc.force_arrangement:
		return
	frappe.db.set_value(
		"Force Arrangement", doc.force_arrangement,
		{"strength_pct": doc.strength_pct_after, "last_observed": doc.report_datetime},
		update_modified=False,
	)


@frappe.whitelist()
def cumulative_losses(force_arrangement: str, days: int = 30):
	rows = frappe.db.sql(
		"""
		SELECT DATE(report_datetime) AS day,
			   SUM(total_kia) AS kia,
			   SUM(total_wia) AS wia
		FROM `tabCasualty Report`
		WHERE force_arrangement = %s
		  AND docstatus = 1
		  AND report_datetime >= DATE_SUB(NOW(), INTERVAL %s DAY)
		GROUP BY DATE(report_datetime)
		ORDER BY day
		""",
		(force_arrangement, days),
		as_dict=True,
	)
	return {
		"series": rows,
		"total_kia": sum(cint(r.kia) for r in rows),
		"total_wia": sum(cint(r.wia) for r in rows),
	}
