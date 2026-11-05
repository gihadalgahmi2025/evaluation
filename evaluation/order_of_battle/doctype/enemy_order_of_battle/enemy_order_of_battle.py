# Copyright (c) 2026, Aljahmi and contributors
# For license information, please see license.txt
"""Enemy Order of Battle (EOB) - the doctrinal tree of the enemy force.

Distinct from ``Force Arrangement`` (which holds the *observed* state): the EOB
is the reference structure, ``Force Arrangement`` is the live picture linked to
it through ``linked_force_arrangement``.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt

from evaluation.evaluation.mixins import CodeMixin

VALID_CONFIDENCE = ("Confirmed", "Probable", "Doubtful")


class EnemyOrderofBattle(CodeMixin, Document):
	def validate(self):
		validate_ob(self, None)

	def on_update(self):
		roll_up_strength(self)

	@frappe.whitelist()
	def link_force_arrangement(self, force_arrangement: str):
		"""Attach a live observed unit to this EOB node."""
		if not frappe.db.exists("Force Arrangement", force_arrangement):
			frappe.throw(_("Force Arrangement {0} does not exist").format(force_arrangement))
		frappe.db.set_value("Force Arrangement", force_arrangement, "linked_enemy_ob", self.name)
		self.linked_force_arrangement = force_arrangement
		self.save()
		return self.name


def validate_ob(doc, method=None):
	if doc.parent_enemy_ob == doc.name:
		frappe.throw(_("A node cannot be its own parent"))

	if doc.confidence_level and doc.confidence_level not in VALID_CONFIDENCE:
		frappe.throw(_("Invalid confidence level"))

	if flt(doc.estimated_strength) < 0:
		frappe.throw(_("Estimated strength cannot be negative"))

	if doc.latitude and not (-90 <= flt(doc.latitude) <= 90):
		frappe.throw(_("Latitude must be between -90 and 90"))
	if doc.longitude and not (-180 <= flt(doc.longitude) <= 180):
		frappe.throw(_("Longitude must be between -180 and 180"))

	# inherit the evaluation unit from the parent
	if not doc.evaluation_unit and doc.parent_enemy_ob:
		doc.evaluation_unit = frappe.db.get_value(
			"Enemy Order of Battle", doc.parent_enemy_ob, "evaluation_unit"
		)

	if doc.parent_enemy_ob:
		parent_group = frappe.db.get_value(
			"Enemy Order of Battle", doc.parent_enemy_ob, "is_group"
		)
		if not cint(parent_group):
			frappe.db.set_value("Enemy Order of Battle", doc.parent_enemy_ob, "is_group", 1,
								update_modified=False)


def roll_up_strength(doc):
	"""Parent nodes hold the sum of their children's estimated strength."""
	if not doc.is_group:
		return
	children = frappe.get_all(
		"Enemy Order of Battle",
		filters={"parent_enemy_ob": doc.name},
		fields=["estimated_strength"],
	)
	total = sum(cint(c.estimated_strength) for c in children)
	if total and cint(doc.estimated_strength) != total:
		frappe.db.set_value("Enemy Order of Battle", doc.name, "estimated_strength", total,
							update_modified=False)


@frappe.whitelist()
def import_orbat(rows: list[dict]):
	"""Bulk-create an order of battle from ``[{name, parent, strength, type}]``."""
	created = 0
	for row in rows:
		if frappe.db.exists("Enemy Order of Battle", row["name"]):
			continue
		doc = frappe.get_doc(
			{
				"doctype": "Enemy Order of Battle",
				"unit_name": row["name"],
				"parent_enemy_ob": row.get("parent"),
				"estimated_strength": row.get("strength") or 0,
				"unit_type": row.get("type"),
				"evaluation_unit": row.get("evaluation_unit"),
			}
		)
		doc.flags.ignore_permissions = True
		doc.insert()
		created += 1
	frappe.db.commit()
	return created
