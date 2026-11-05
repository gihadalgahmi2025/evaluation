# Copyright (c) 2026, Aljahmi and contributors
# For license information, please see license.txt
"""Situation Report (SITREP) - a point-in-time snapshot of the battlefield."""

from __future__ import annotations

import hashlib
import json

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, get_datetime, now_datetime


class SituationReport(Document):
	def validate(self):
		validate_sitrep(self, None)

	def on_submit(self):
		update_force_state(self, None)

	@frappe.whitelist()
	def capture_snapshot(self):
		"""Freeze the current state of the sector's units into snapshot lines."""
		self.set("snapshot_lines", [])
		units = frappe.get_all(
			"Force Arrangement",
			filters={
				"evaluation_unit": self.evaluation_unit,
				"is_group": 0,
			},
			fields=["name", "current_posture", "strength_pct", "latitude", "longitude"],
		)
		if self.sector:
			units = [u for u in units if u.name == self.sector]

		for unit in units:
			self.append(
				"snapshot_lines",
				{
					"force_arrangement": unit.name,
					"posture": unit.current_posture,
					"strength_pct": unit.strength_pct,
					"latitude": unit.latitude,
					"longitude": unit.longitude,
				},
			)
		self.map_snapshot_hash = hashlib.md5(
			json.dumps([u.name for u in units], sort_keys=True).encode()
		).hexdigest()[:12]
		return len(self.snapshot_lines)


def validate_sitrep(doc, method=None):
	if not doc.report_datetime:
		doc.report_datetime = now_datetime()
	if get_datetime(doc.report_datetime) > now_datetime():
		frappe.throw(_("Report datetime cannot be in the future"))

	seen = set()
	for row in doc.snapshot_lines:
		if row.force_arrangement in seen:
			frappe.throw(
				_("Row {0}: unit {1} appears twice in the snapshot").format(
					row.idx, row.force_arrangement
				)
			)
		seen.add(row.force_arrangement)

	if not doc.evaluation_unit and doc.sector:
		doc.evaluation_unit = frappe.db.get_value(
			"Force Arrangement", doc.sector, "evaluation_unit"
		)


def update_force_state(doc, method=None):
	"""Write the snapshot back onto the observed units (posture + strength)."""
	for row in doc.snapshot_lines:
		values = {}
		if row.posture:
			values["current_posture"] = row.posture
		if flt(row.strength_pct):
			values["strength_pct"] = flt(row.strength_pct)
		values["last_sitrep"] = doc.name
		if values:
			frappe.db.set_value("Force Arrangement", row.force_arrangement, values,
								update_modified=False)

	if doc.sector:
		frappe.db.set_value("Force Arrangement", doc.sector, "last_sitrep", doc.name,
							update_modified=False)


@frappe.whitelist()
def compare_sitreps(older: str, newer: str):
	"""Diff two SITREPs - returns changed units per field."""
	a = {r.force_arrangement: r for r in frappe.get_doc("Situation Report", older).snapshot_lines}
	b = {r.force_arrangement: r for r in frappe.get_doc("Situation Report", newer).snapshot_lines}

	changes = []
	for unit in sorted(set(a) | set(b)):
		before, after = a.get(unit), b.get(unit)
		if not before or not after:
			changes.append({"unit": unit, "change": "added" if after else "removed"})
			continue
		diffs = {}
		if before.posture != after.posture:
			diffs["posture"] = [before.posture, after.posture]
		if flt(before.strength_pct) != flt(after.strength_pct):
			diffs["strength_pct"] = [before.strength_pct, after.strength_pct]
		if diffs:
			changes.append({"unit": unit, "changes": diffs})
	return changes
