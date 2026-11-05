# Copyright (c) 2026, Aljahmi and contributors
# For license information, please see license.txt
"""
Shared controller mixins for the Evaluation app.

These mixins centralise behaviour that every master/reference DocType in this
app needs, so individual controllers stay small and consistent:

* :class:`MasterRecord` - reference (lookup) tables such as Military Rank,
  Target Type, Supply Class ... It normalises the title field, keeps an
  optional "is_active" flag in sync and blocks deletion while the record is
  still referenced elsewhere.
* :class:`CodeMixin`   - deterministic, human readable codes derived from a name.
"""

from __future__ import annotations

import re

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, cstr, strip_html

WHITESPACE_RE = re.compile(r"\s+")
ARABIC_DIACRITICS_RE = re.compile(r"[\u0617-\u061A\u064B-\u0652]")


class CodeMixin:
	"""Helpers to build stable, readable codes from arbitrary text."""

	#: characters that are transliterated before falling back to the raw text
	TRANSLITERATION = {
		"أ": "a", "إ": "e", "آ": "a", "ا": "a", "ب": "b", "ت": "t", "ث": "th",
		"ج": "j", "ح": "h", "خ": "kh", "د": "d", "ذ": "dh", "ر": "r", "ز": "z",
		"س": "s", "ش": "sh", "ص": "s", "ض": "d", "ط": "t", "ظ": "z", "ع": "a",
		"غ": "gh", "ف": "f", "ق": "q", "ك": "k", "ل": "l", "م": "m", "ن": "n",
		"ه": "h", "و": "w", "ي": "y", "ى": "a", "ة": "h", "ء": "", "ئ": "e",
		"ؤ": "o", "ـ": "",
	}

	@staticmethod
	def make_code(value: str, max_length: int = 30, separator: str = "-") -> str:
		"""Return an upper-case ASCII code for *value* (``"3rd Armoured"`` -> ``3RD-ARMOURED``)."""
		value = ARABIC_DIACRITICS_RE.sub("", cstr(value))
		value = "".join(CodeMixin.TRANSLITERATION.get(ch, ch) for ch in value)
		value = re.sub(r"[^0-9A-Za-z]+", separator, value).strip(separator)
		return value.upper()[:max_length].strip(separator)


class MasterRecord(CodeMixin, Document):
	"""Base controller for the reference tables of the app.

	Subclasses normally only define ``title_field``.  Everything else (title
	normalisation, active flag handling, link-safe deletion) is inherited.
	"""

	#: field holding the human readable value of the record
	title_field: str | None = None

	#: optional checkbox that marks a record as usable / retired
	active_field: str = "is_active"

	#: raise instead of silently allowing a referenced record to be deleted
	prevent_delete_if_linked: bool = True

	# ------------------------------------------------------------------ hooks
	def validate(self):
		self.normalize_title()
		self.set_missing_active_flag()

	def normalize_title(self):
		"""Trim and collapse whitespace in every short text field of the record."""
		for df in self.meta.fields:
			if df.fieldtype not in ("Data", "Small Text", "Select"):
				continue
			value = self.get(df.fieldname)
			if isinstance(value, str) and value:
				clean = WHITESPACE_RE.sub(" ", strip_html(value)).strip()
				if clean != value:
					self.set(df.fieldname, clean)

	def set_missing_active_flag(self):
		if self.active_field and self.meta.has_field(self.active_field):
			if self.get(self.active_field) is None:
				self.set(self.active_field, 1)

	def before_delete(self):
		if not self.prevent_delete_if_linked:
			return
		self.guard_against_links()

	def on_trash(self):
		# Frappe already blocks deletion of linked documents in most cases; the
		# explicit check below produces a friendly message instead of a raw DB error.
		self.guard_against_links()

	# ---------------------------------------------------------------- helpers
	def guard_against_links(self):
		"""Raise a readable error when *self* is referenced by another document."""
		linked = find_links(self.doctype, self.name)
		if not linked:
			return

		details = _summarise_links(linked)
		frappe.throw(
			_("Cannot delete {0} <b>{1}</b>: it is linked to {2}.<br>Deactivate it instead.").format(
				_(self.doctype), frappe.utils.escape_html(self.name), details
			),
			title=_("Record in use"),
		)

	def get_title_value(self) -> str:
		"""Return the configured title field value (falls back to ``doc.name``)."""
		if self.title_field and self.meta.has_field(self.title_field):
			return cstr(self.get(self.title_field)) or self.name
		return self.name


@frappe.whitelist()
def find_links(doctype: str, name: str, limit: int = 20) -> list[dict]:
	"""Return documents that reference ``doctype/name`` through a Link field.

	The result is capped at ``limit`` rows so the check stays cheap on big sites;
	child tables are reported with their parent DocType.
	"""
	link_fields = get_link_fields(doctype)
	if not link_fields:
		return []

	found: list[dict] = []
	seen: set[tuple[str, str]] = set()

	for df in link_fields:
		if df.parent == doctype:
			# self referencing tree/link fields are expected, ignore them
			continue

		rows = frappe.get_all(
			df.parent,
			filters={df.fieldname: name},
			fields=["name"],
			limit_page_length=limit,
			ignore_permissions=True,
			distinct=True,
		)
		if not rows:
			continue

		key = (df.parent, df.fieldname)
		if key in seen:
			continue
		seen.add(key)
		found.append(
			{
				"doctype": df.parent,
				"field": df.fieldname,
				"count": len(rows),
				"names": [r.name for r in rows],
			}
		)
	return found


def get_link_fields(doctype: str) -> list:
	"""Cached list of (standard + custom) Link fields pointing at *doctype*."""
	cache = frappe.cache()
	key = f"evaluation:link_fields:{doctype}"
	fields = cache.get_value(key)
	if fields is not None:
		return [frappe._dict(f) for f in fields]

	def collect():
		out = []
		for row in frappe.get_all(
			"DocField",
			filters={"fieldtype": "Link", "options": doctype},
			fields=["parent", "fieldname"],
			ignore_permissions=True,
		):
			out.append({"parent": row.parent, "fieldname": row.fieldname})
		for row in frappe.get_all(
			"Custom Field",
			filters={"fieldtype": "Link", "options": doctype},
			fields=["dt as parent", "fieldname"],
			ignore_permissions=True,
		):
			out.append({"parent": row.parent, "fieldname": row.fieldname})
		return out

	fields = collect()
	cache.set_value(key, fields, expires_in_sec=3600)
	return [frappe._dict(f) for f in fields]


def _summarise_links(links: list[dict], max_items: int = 3) -> str:
	parts = []
	for row in links[:max_items]:
		names = ", ".join(row["names"][:3])
		parts.append(_("{0} ({1})").format(_(row["doctype"]), frappe.utils.escape_html(names)))
	suffix = "" if len(links) <= max_items else _(" and {0} more").format(len(links) - max_items)
	return "; ".join(parts) + suffix


def clear_link_cache(doc=None, method=None):
	"""``on_update``/``after_delete`` hook target: drop cached link lookups."""
	try:
		frappe.cache().delete_keys("evaluation:link_fields")
	except Exception:
		frappe.clear_cache()


__all__ = ["CodeMixin", "MasterRecord", "find_links", "get_link_fields", "clear_link_cache", "cint"]
