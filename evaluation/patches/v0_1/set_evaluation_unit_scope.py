# Copyright (c) 2026, Aljahmi and contributors
# For license information, please see license.txt
"""v0.1 - backfill ``evaluation_unit`` on documents created before it existed."""

from __future__ import annotations

import frappe


def execute():
	"""Copy the missing evaluation unit from the linked observed unit."""
	pairs = [
		# (doctype, source field holding a Force Arrangement, target field)
		("Daily Activities", "military_division", "evaluation_unit"),
		("Intel Report", "observed_force", "evaluation_unit"),
		("Target", "assigned_unit", "evaluation_unit"),
		("Situation Report", "sector", "evaluation_unit"),
		("Threat Assessment", "sector", "evaluation_unit"),
	]

	for doctype, source_field, target_field in pairs:
		if not frappe.db.table_exists(doctype):
			continue
		if not frappe.db.has_column(doctype, target_field):
			continue

		rows = frappe.db.sql(
			f"""
			SELECT d.name, f.evaluation_unit
			FROM `tab{doctype}` d
			INNER JOIN `tabForce Arrangement` f ON f.name = d.{source_field}
			WHERE (d.{target_field} IS NULL OR d.{target_field} = '')
			  AND f.evaluation_unit IS NOT NULL
			""",
			as_dict=True,
		)
		for row in rows:
			frappe.db.set_value(doctype, row.name, target_field, row.evaluation_unit,
								update_modified=False)
		print(f"  {doctype}: {len(rows)} rows backfilled")

	frappe.db.commit()
