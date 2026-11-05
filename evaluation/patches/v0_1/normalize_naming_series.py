# Copyright (c) 2026, Aljahmi and contributors
# For license information, please see license.txt
"""v0.1 - normalise legacy naming series such as ``INT-.YYYY.-`` to ``INT-.YYYY.#####``."""

from __future__ import annotations

import frappe

FIXES = {
	"Target": "TGT-.#####",
	"Threat Assessment": "THR-.YYYY.#####",
	"Daily Activities": "DA-ACTIV.-.#####",
	"Insulation": "GDI.-.#####",
	"Situation Report": "SITREP-.YYYY.#####",
	"Intel Report": "INT-.YYYY.#####",
	"Force Arrangement": "EV-AOF-",
	"Operation Order": "OPORD-.YYYY.#####",
	"Personality": "HR-EMP-.#####",
	"Casualty Report": "CAS-.YYYY.#####",
}


def execute():
	for doctype, series in FIXES.items():
		if not frappe.db.table_exists(doctype):
			continue
		df = frappe.db.get_value(
			"DocField", {"parent": doctype, "fieldname": "naming_series"}, "fieldname"
		)
		if not df:
			continue
		frappe.db.sql(
			"""
			UPDATE `tabDocField`
			SET options = %s, default = %s
			WHERE parent = %s AND fieldname = 'naming_series'
			""",
			(series, series, doctype),
		)
		frappe.db.sql(
			"""
			UPDATE `tabProperty Setter`
			SET value = %s
			WHERE doc_type = %s AND field_name = 'naming_series' AND property = 'options'
			""",
			(series, doctype),
		)
	frappe.db.commit()
