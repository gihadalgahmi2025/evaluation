# Copyright (c) 2026, Aljahmi and contributors
# For license information, please see license.txt
"""v0.1 - drop the duplicate Geolocation columns that shadowed real tables."""

from __future__ import annotations

import frappe

LEGACY = {
	"Force Arrangement": [
		"geographic_spread",
		"tactice_spread",
		"managemente_spread",
		"move_method_used",
		"force_arrangement",
		"section_break_lrlp",
		"managemen_spread_section",
		"army_chief_section",
	],
	"Division Type Row": ["amended_from"],
}


def execute():
	for doctype, fields in LEGACY.items():
		if not frappe.db.table_exists(doctype):
			continue
		for field in fields:
			if frappe.db.has_column(doctype, field):
				frappe.db.sql_ddl(f"ALTER TABLE `tab{doctype}` DROP COLUMN `{field}`")
			frappe.db.delete("DocField", {"parent": doctype, "fieldname": field})
			frappe.db.delete("Property Setter",
							 {"doc_type": doctype, "field_name": field})
			frappe.db.delete("Custom Field", {"dt": doctype, "fieldname": field})
			print(f"  dropped {doctype}.{field}")

	frappe.db.commit()
