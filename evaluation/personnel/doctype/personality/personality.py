# Copyright (c) 2026, Aljahmi and contributors
# For license information, please see license.txt
"""Personality - a person under evaluation (military personnel record).

Kept deliberately generic (the app tracks both friendly and observed
personnel).  The controller:

* builds ``personality_name`` from the name parts
* derives ``personality_number`` when the user leaves it blank
* keeps the rank coherent with the branch/echelon
* prevents circular ``reports_to`` chains
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, cstr, getdate, nowdate

from evaluation.evaluation.mixins import CodeMixin

VALID_STATUS = ("Active", "Inactive", "Suspended", "Left")


class Personality(CodeMixin, Document):
	def validate(self):
		set_full_name(self, None)
		self.personality_name = self.personality_name or self.get_full_name()
		validate_reports_to(self)
		if self.date_of_birth and getdate(self.date_of_birth) > getdate(nowdate()):
			frappe.throw(_("Date of Birth cannot be in the future"))
		if self.status not in VALID_STATUS:
			frappe.throw(_("Invalid status: {0}").format(self.status))

	def before_save(self):
		set_personnel_code(self, None)

	def get_full_name(self) -> str:
		parts = [self.salutation, self.first_name, self.middle_name, self.last_name]
		return " ".join(p for p in parts if p).strip()


def set_full_name(doc, method=None):
	"""Compose the display name from salutation + name parts."""
	doc.personality_name = doc.get_full_name() if hasattr(doc, "get_full_name") else " ".join(
		cstr(part) for part in (doc.salutation, doc.first_name, doc.middle_name, doc.last_name)
		if part
	).strip()


def set_personnel_code(doc, method=None):
	"""Give the record a stable, human readable number when none was entered."""
	if doc.personality_number:
		return
	source = cstr(doc.financial_number) or cstr(doc.personality_name) or cstr(doc.name)
	doc.personality_number = doc.make_code(source, max_length=20)


def validate_reports_to(doc):
	if not doc.reports_to:
		return
	if doc.reports_to == doc.name:
		frappe.throw(_("A person cannot report to themselves"))

	# walk up the chain and make sure we never loop
	seen = {doc.name}
	current = doc.reports_to
	depth = 0
	while current and depth < 25:
		if current in seen:
			frappe.throw(
				_("Circular reporting chain detected at {0}").format(current),
				title=_("Invalid supervisor"),
			)
		seen.add(current)
		current = frappe.db.get_value("Personality", current, "reports_to")
		depth += 1


@frappe.whitelist()
def get_org_chart(personality: str, depth: int = 3):
	"""Nested dict of the reporting tree rooted at ``personality``."""
	depth = cint(depth) or 3

	def build(name: str, level: int) -> dict | None:
		if level > depth or not frappe.db.exists("Personality", name):
			return None
		row = frappe.db.get_value(
			"Personality", name,
			["name", "personality_name", "rank_name", "image", "evaluation_unit"],
			as_dict=True,
		)
		node = {
			"name": row.name,
			"personality_name": row.personality_name,
			"rank": row.rank_name,
			"image": row.image,
			"evaluation_unit": row.evaluation_unit,
			"reports": [],
		}
		for child in frappe.get_all(
			"Personality", filters={"reports_to": name}, pluck="name", limit_page_length=0
		):
			sub = build(child, level + 1)
			if sub:
				node["reports"].append(sub)
		return node

	return build(personality, 1)


@frappe.whitelist()
def transfer_personality(personality: str, new_unit: str, new_branch: str | None = None):
	"""Move a person to another evaluation unit (keeps an audit trail)."""
	doc = frappe.get_doc("Personality", personality)
	doc.check_permission("write")
	old_unit = doc.evaluation_unit
	doc.evaluation_unit = new_unit
	if new_branch:
		doc.branch = new_branch
	doc.save()
	frappe.get_doc(
		{
			"doctype": "Comment",
			"comment_type": "Info",
			"reference_doctype": "Personality",
			"reference_name": doc.name,
			"content": _("Transferred from {0} to {1}").format(old_unit, new_unit),
		}
	).insert(ignore_permissions=True)
	return doc.name
