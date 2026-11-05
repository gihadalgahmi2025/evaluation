# Copyright (c) 2026, Aljahmi and contributors
# For license information, please see license.txt
"""Row level permissions for the Evaluation app.

The app has three layers of access:

1. **Role permissions** (declared on every DocType) - who may read/write the
   doctype at all.
2. **Evaluation Unit scoping** - a user assigned to one or more Evaluation Units
   only sees records belonging to those units (and their descendants).
3. **Classification gating** - only users with an Intel/Officer role may read
   raw coordinates or un-redacted intel.

All functions below are wired into ``hooks.py`` (``permission_query_conditions``
and ``has_permission``) and can be called directly from controllers.
"""

from __future__ import annotations

import frappe
from frappe import _

SCOPE_EXEMPT_ROLES = {"System Manager", "Administrator", "Evaluation Manager"}
INTEL_ROLES = {
	"System Manager",
	"Administrator",
	"Evaluation Manager",
	"Evaluation Commander",
	"Evaluation Intel Officer",
}

#: session key used to cache the resolved unit scope for the current user
_SCOPE_CACHE_KEY = "evaluation_unit_scope"


# ---------------------------------------------------------------------------
# Scope resolution
# ---------------------------------------------------------------------------
def get_user_units(user: str | None = None) -> list[str]:
	"""Evaluation Units the user may see.

	Resolution order:

	1. ``System Manager`` / ``Evaluation Manager`` -> all units (empty list means
	   "no restriction").
	2. ``Evaluation Unit`` child table on the User document (field
	   ``evaluation_units``) -> explicit assignment.
	3. Fallback: units where the user's linked Personality works.
	"""
	user = user or frappe.session.user
	roles = set(frappe.get_roles(user))
	if roles & SCOPE_EXEMPT_ROLES:
		return []

	cache_key = f"{_SCOPE_CACHE_KEY}:{user}"
	cached = frappe.cache.get_value(cache_key)
	if cached is not None:
		return cached

	units: list[str] = []

	# explicit assignment on the user record (custom field, created in setup.py)
	if frappe.db.has_column("User", "evaluation_units"):
		assigned = frappe.db.get_value("User", user, "evaluation_units")
		if assigned:
			units = [u.strip() for u in assigned.split(",") if u.strip()]

	# fallback: through the linked personnel record
	if not units:
		person = frappe.db.get_value("Personality", {"user": user}, "evaluation_unit")
		if person:
			units = [person]

	# expand to descendants so a parent-unit user sees child units too
	expanded: list[str] = []
	for unit in units:
		expanded.append(unit)
		row = frappe.db.get_value("Evaluation Unit", unit, ["lft", "rgt"], as_dict=True)
		if row:
			expanded.extend(
				d.name
				for d in frappe.get_all(
					"Evaluation Unit",
					filters={"lft": (">", row.lft), "rgt": ("<", row.rgt)},
					fields=["name"],
				)
			)

	units = sorted(set(expanded))
	frappe.cache.set_value(cache_key, units, expires_in_sec=3600)
	return units


def clear_scope_cache(doc=None, method=None):
	"""Drop the cached unit scope of every user (called on User/Unit changes)."""
	try:
		keys = frappe.cache.get_keys(f"*{_SCOPE_CACHE_KEY}*") or []
		for key in keys:
			frappe.cache.delete_value(key)
	except Exception:
		pass


def _scope_condition(doctype: str, user: str | None = None) -> str | None:
	"""Build a ``tabX.evaluation_unit in (...)`` SQL fragment or ``None``."""
	units = get_user_units(user)
	if not units:
		return None

	if not frappe.db.has_column(doctype, "evaluation_unit"):
		return None

	values = ", ".join(frappe.db.escape(u) for u in units)
	return f"`tab{doctype}`.`evaluation_unit` in ({values})"


# ---------------------------------------------------------------------------
# Permission query conditions (list view / reports)
# ---------------------------------------------------------------------------
def daily_activities_query(user: str | None = None) -> str:
	return _scope_condition("Daily Activities", user) or ""


def intel_report_query(user: str | None = None) -> str:
	return _scope_condition("Intel Report", user) or ""


def target_query(user: str | None = None) -> str:
	return _scope_condition("Target", user) or ""


# ---------------------------------------------------------------------------
# has_permission hooks (single document access)
# ---------------------------------------------------------------------------
def _has_unit_access(doctype: str, docname: str | None, user: str | None = None) -> bool | None:
	"""``None`` means "no opinion, fall through to role permissions"."""
	if not docname:
		return None
	units = get_user_units(user)
	if not units:
		return None
	unit = frappe.db.get_value(doctype, docname, "evaluation_unit")
	if not unit:
		return None
	return unit in units


def has_activity_permission(doc, ptype=None, user=None, debug=False):
	return _has_unit_access("Daily Activities", getattr(doc, "name", None), user)


def has_intel_permission(doc, ptype=None, user=None, debug=False):
	return _has_unit_access("Intel Report", getattr(doc, "name", None), user)


def has_target_permission(doc, ptype=None, user=None, debug=False):
	return _has_unit_access("Target", getattr(doc, "name", None), user)


# ---------------------------------------------------------------------------
# Classification helpers used by controllers
# ---------------------------------------------------------------------------
def can_view_precise_coordinates(user: str | None = None) -> bool:
	return bool(set(frappe.get_roles(user or frappe.session.user)) & INTEL_ROLES)


def scrub_doc_for_user(doc, user: str | None = None):
	"""Mask sensitive fields in place when the user lacks clearance."""
	if can_view_precise_coordinates(user):
		return doc

	if doc.meta.has_field("latitude"):
		doc.latitude = None
	if doc.meta.has_field("longitude"):
		doc.longitude = None
	if doc.meta.has_field("mgrs"):
		doc.mgrs = None
	return doc


def require_role(*roles: str):
	"""Decorator - raise :class:`frappe.PermissionError` when role is missing."""

	def wrapper(fn):
		def inner(*args, **kwargs):
			if not set(frappe.get_roles()) & set(roles):
				frappe.throw(
					_("You need one of these roles to continue: {0}").format(", ".join(roles)),
					frappe.PermissionError,
				)
			return fn(*args, **kwargs)

		inner.__name__ = fn.__name__
		inner.__doc__ = fn.__doc__
		return inner

	return wrapper


__all__ = [
	"get_user_units",
	"clear_scope_cache",
	"daily_activities_query",
	"intel_report_query",
	"target_query",
	"has_activity_permission",
	"has_intel_permission",
	"has_target_permission",
	"can_view_precise_coordinates",
	"scrub_doc_for_user",
	"require_role",
]
