# Copyright (c) 2026, Aljahmi and contributors
# For license information, please see license.txt
"""Evaluation Unit - the friendly organisation tree that owns all data.

Every transactional document carries an ``evaluation_unit``; this tree drives
row level permissions (see :mod:`evaluation.permissions`).
"""

from __future__ import annotations

import frappe
from frappe import _

from evaluation.evaluation.mixins import MasterRecord


class EvaluationUnit(MasterRecord):
	title_field = "unit_name"
	active_field = "is_default"
	prevent_delete_if_linked = True

	def validate(self):
		super().validate()
		# only one default unit may exist
		if self.is_default:
			others = frappe.get_all(
				"Evaluation Unit",
				filters={"is_default": 1, "name": ("!=", self.name)},
				pluck="name",
			)
			for other in others:
				frappe.db.set_value("Evaluation Unit", other, "is_default", 0,
									update_modified=False)

		if self.abbreviation:
			self.abbreviation = self.abbreviation.strip().upper()[:10]
			duplicate = frappe.db.exists(
				"Evaluation Unit",
				{"abbreviation": self.abbreviation, "name": ("!=", self.name)},
			)
			if duplicate:
				frappe.throw(
					_("Abbreviation {0} is already used by {1}").format(
						self.abbreviation, duplicate
					)
				)


@frappe.whitelist()
def get_default_unit() -> str | None:
	return frappe.db.get_value("Evaluation Unit", {"is_default": 1}, "name")
