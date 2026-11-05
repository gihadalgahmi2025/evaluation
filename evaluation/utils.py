# Copyright (c) 2026, Aljahmi and contributors
# For license information, please see license.txt
"""Shared helpers for the Evaluation app.

Everything that more than one DocType needs lives here so controllers stay
thin.  Functions are written to be safe to call from the desk, from background
jobs and from the REST API.
"""

from __future__ import annotations

import math
from typing import Iterable

import frappe
from frappe import _
from frappe.utils import (
	add_days,
	cint,
	cstr,
	flt,
	get_datetime,
	getdate,
	now_datetime,
	time_diff_in_seconds,
)

# ---------------------------------------------------------------------------
# Constants shared across the app
# ---------------------------------------------------------------------------
CONFIDENCE_LEVELS = ("Confirmed", "Probable", "Doubtful")
CONFIDENCE_WEIGHT = {"Confirmed": 1.0, "Probable": 0.7, "Doubtful": 0.4}

THREAT_LEVELS = ("Low", "Medium", "High", "Critical")
THREAT_CUTOFFS = ((0.75, "Critical"), (0.55, "High"), (0.30, "Medium"), (0.0, "Low"))

TARGET_PRIORITIES = ("Critical", "High", "Medium", "Low")
PRIORITY_SCORE_RANGE = {"Critical": (90, 100), "High": (70, 89), "Medium": (40, 69), "Low": (0, 39)}

CHILD_TABLE_FIELDS = {"Table", "Table MultiSelect"}


# ---------------------------------------------------------------------------
# Generic hooks (attached to "*" in hooks.py)
# ---------------------------------------------------------------------------
def validate_common_rules(doc, method=None):
	"""Universal guard rails applied to every document in the app.

	* strips trailing spaces from text fields so joins stay reliable
	* rejects dates in the impossible future (data entry mistakes)
	* keeps ``is_active`` style flags sane
	"""
	for df in doc.meta.fields:
		if df.fieldtype in ("Data", "Small Text") and isinstance(doc.get(df.fieldname), str):
			value = doc.get(df.fieldname)
			if value != value.strip():
				doc.set(df.fieldname, value.strip())

	if doc.meta.has_field("valid_from") and doc.meta.has_field("valid_until"):
		if doc.get("valid_from") and doc.get("valid_until"):
			if get_datetime(doc.valid_until) < get_datetime(doc.valid_from):
				frappe.throw(_("Valid Until cannot be earlier than Valid From"))

	if doc.meta.has_field("period_from") and doc.meta.has_field("period_to"):
		if doc.get("period_from") and doc.get("period_to"):
			if getdate(doc.period_to) < getdate(doc.period_from):
				frappe.throw(_("Period To cannot be earlier than Period From"))


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------
def get_force_display_name(force_arrangement: str | None) -> str:
	"""Return ``Unit Name (echelon)`` for a Force Arrangement record."""
	if not force_arrangement:
		return ""
	row = frappe.db.get_value(
		"Force Arrangement", force_arrangement, ["name_div", "size_div"], as_dict=True
	)
	if not row:
		return force_arrangement
	return f"{row.name_div}" + (f" ({row.size_div})" if row.size_div else "")


def get_readiness_color(value: float | None) -> str:
	"""Traffic-light colour for a readiness percentage."""
	value = flt(value)
	if value >= 80:
		return "green"
	if value >= 60:
		return "orange"
	return "red"


def get_unit_strength(force_arrangement: str, as_of: str | None = None) -> float:
	"""Current strength percentage of an observed enemy unit."""
	return flt(
		frappe.db.get_value("Force Arrangement", force_arrangement, "strength_pct") or 0
	)


def mask_coordinates(value, precision: int = 3) -> str:
	"""Reduce coordinate precision for users without clearance."""
	try:
		return f"{round(flt(value), precision)}"
	except Exception:
		return cstr(value)


def format_mgrs(value) -> str:
	"""Pretty print an MGRS string.

	``38SMB45217834`` -> ``38S MB 4521 7834`` (zone+band, 100km square,
	easting, northing).  Short or malformed values are returned unchanged so the
	helper is always safe to use in a print format.
	"""
	text = cstr(value).replace(" ", "").upper()
	if len(text) < 7:
		return text

	zone = text[:2]
	band = text[2]
	square = text[3:5]
	rest = text[5:]
	if len(rest) % 2:
		return f"{zone}{band} {square} {rest}"
	half = len(rest) // 2
	return f"{zone}{band} {square} {rest[:half]} {rest[half:]}"


# ---------------------------------------------------------------------------
# Formatting / parsing helpers
# ---------------------------------------------------------------------------
def pct(part: float, total: float, ndigits: int = 2) -> float:
	"""Safe percentage helper (never raises on zero totals)."""
	total = flt(total)
	if not total:
		return 0.0
	return round(flt(part) * 100.0 / total, ndigits)


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
	return max(low, min(high, flt(value)))


def weighted_average(pairs: Iterable[tuple[float, float]]) -> float:
	"""``pairs`` is an iterable of ``(value, weight)`` tuples."""
	total_weight = 0.0
	total = 0.0
	for value, weight in pairs:
		weight = flt(weight)
		if weight <= 0:
			continue
		total += flt(value) * weight
		total_weight += weight
	return round(total / total_weight, 2) if total_weight else 0.0


def days_between(later, earlier) -> int:
	if not later or not earlier:
		return 0
	delta = get_datetime(later) - get_datetime(earlier)
	return int(delta.total_seconds() // 86400)


def is_stale(last_seen, max_age_hours: int = 48) -> bool:
	"""True when a record has not been refreshed within ``max_age_hours``."""
	if not last_seen:
		return True
	return time_diff_in_seconds(now_datetime(), get_datetime(last_seen)) > max_age_hours * 3600


def freshness_label(last_seen) -> str:
	"""Human label used on lists / dashboards."""
	if not last_seen:
		return _("Never observed")
	hours = int(time_diff_in_seconds(now_datetime(), get_datetime(last_seen)) // 3600)
	if hours < 1:
		return _("Fresh (under 1 hour)")
	if hours < 24:
		return _("{0} hours ago").format(hours)
	return _("{0} days ago").format(hours // 24)


def haversine_km(lat1, lon1, lat2, lon2) -> float:
	"""Great-circle distance in kilometres between two points."""
	try:
		lat1, lon1, lat2, lon2 = map(math.radians, (flt(lat1), flt(lon1), flt(lat2), flt(lon2)))
	except Exception:
		return 0.0
	dlat, dlon = lat2 - lat1, lon2 - lon1
	a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
	return round(2 * 6371 * math.asin(math.sqrt(a)), 2)


# ---------------------------------------------------------------------------
# Tree / hierarchy helpers
# ---------------------------------------------------------------------------
def get_descendants(doctype: str, name: str) -> list[str]:
	"""All descendant names of a nested set record, excluding itself."""
	row = frappe.db.get_value(doctype, name, ["lft", "rgt"], as_dict=True)
	if not row:
		return []
	return [
		d.name
		for d in frappe.get_all(
			doctype,
			filters={"lft": (">", row.lft), "rgt": ("<", row.rgt)},
			fields=["name"],
			order_by="lft asc",
		)
	]


def get_ancestors(doctype: str, name: str) -> list[str]:
	row = frappe.db.get_value(doctype, name, ["lft", "rgt"], as_dict=True)
	if not row:
		return []
	return [
		d.name
		for d in frappe.get_all(
			doctype,
			filters={"lft": ("<", row.lft), "rgt": (">", row.rgt)},
			fields=["name"],
			order_by="lft desc",
		)
	]


# ---------------------------------------------------------------------------
# Whitelisted API used by dashboards and the desk UI
# ---------------------------------------------------------------------------
@frappe.whitelist()
def get_dashboard_stats(evaluation_unit: str | None = None):
	"""Aggregate counters rendered on the Evaluation workspace."""
	filters = {"docstatus": 1}
	if evaluation_unit:
		filters["evaluation_unit"] = evaluation_unit

	unit_filter = {"evaluation_unit": evaluation_unit} if evaluation_unit else {}

	# Targets are driven by the Target Approval workflow, so "active" means an
	# approved or submitted record rather than a plain ``status`` column.
	active_target_filters = {**filters}
	if frappe.db.has_column("Target", "status"):
		active_target_filters["status"] = "Active"
	else:
		active_target_filters["workflow_state"] = ("not in", ["Draft", "Rejected", "Closed"])

	# master/workflow driven doctypes are counted while not cancelled
	live = {**unit_filter, "docstatus": ("<", 2)}

	return {
		"targets": frappe.db.count("Target", live),
		"active_targets": frappe.db.count("Target", active_target_filters),
		"daily_activities": frappe.db.count("Daily Activities", filters),
		"open_intel": frappe.db.count("Intel Report", {**unit_filter, "docstatus": 0}),
		"situation_reports": frappe.db.count("Situation Report", filters),
		"threats": frappe.db.count("Threat Assessment", live),
		"observed_units": frappe.db.count("Force Arrangement", unit_filter),
		"personnel": frappe.db.count("Personality", unit_filter),
		"critical_threats": frappe.db.count(
			"Threat Assessment", {**unit_filter, "overall_threat_level": "Critical"}
		),
		"critical_targets": frappe.db.count(
			"Target", {**unit_filter, "priority": "Critical", "docstatus": ("<", 2)}
		),
	}


@frappe.whitelist()
def search_enemy_forces(txt: str, limit: int = 20):
	"""Type-ahead used by the link fields on recon documents."""
	return frappe.get_all(
		"Force Arrangement",
		or_filters=[["name_div", "like", f"%{txt}%"], ["name", "like", f"%{txt}%"]],
		fields=["name", "name_div", "size_div", "strength_pct", "current_posture"],
		limit_page_length=cint(limit) or 20,
	)


@frappe.whitelist()
def get_unit_hierarchy(force_arrangement: str):
	"""Return the parent chain of an observed unit (for breadcrumbs)."""
	ancestors = get_ancestors("Force Arrangement", force_arrangement)
	return [
		frappe.db.get_value("Force Arrangement", name, ["name", "name_div"], as_dict=True)
		for name in ancestors
	]
