# Copyright (c) 2026, Aljahmi and contributors
# For license information, please see license.txt
"""Boot session payload - small, cached data the desk needs on every page."""

from __future__ import annotations

import frappe

from evaluation.permissions import can_view_precise_coordinates, get_user_units


def boot_session(bootinfo):
	"""Attach evaluation settings to ``frappe.boot``."""
	units = get_user_units()
	bootinfo.evaluation = {
		"units": units,
		"can_view_coordinates": can_view_precise_coordinates(),
		"default_unit": frappe.defaults.get_user_default("evaluation_unit")
		or (units[0] if units else None),
		"postures": frappe.get_all(
			"Combat Posture",
			filters={"is_active": 1},
			fields=["name", "map_color", "symbol_code"],
			order_by="sort_order asc",
			limit_page_length=50,
		),
		"priorities": ["Critical", "High", "Medium", "Low"],
		"confidence": ["Confirmed", "Probable", "Doubtful"],
	}
