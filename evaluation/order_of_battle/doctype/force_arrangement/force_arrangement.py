# Copyright (c) 2026, Aljahmi and contributors
# For license information, please see license.txt
"""Force Arrangement - the observed enemy order of battle (tree).

``Force Arrangement`` is the spine of the app: almost every transactional
document points at one unit.  The controller keeps that spine consistent:

* computes the **combat power index** from readiness, logistics, ammunition
  and strength using the weights in ``Combat Power Weight``
* keeps ``strength_pct`` inside 0-100
* cascades the evaluation unit down the tree
* maintains stale-observation flags
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, getdate, nowdate

from evaluation.utils import clamp, weighted_average

#: fallback weights used when the Combat Power Weight table is empty
DEFAULT_WEIGHTS = {"readiness": 0.35, "logistics": 0.25, "ammunition": 0.20, "strength": 0.20}


class ForceArrangement(Document):
	def validate(self):
		validate_force(self, None)
		self.combat_power_index = compute_combat_power(self)

	def on_update(self):
		propagate_evaluation_unit(self)

	# ------------------------------------------------------------------ api
	@frappe.whitelist()
	def refresh_index(self) -> float:
		"""Recompute and persist the combat power index."""
		self.combat_power_index = compute_combat_power(self)
		self.db_set("combat_power_index", self.combat_power_index, update_modified=False)
		return self.combat_power_index

	@frappe.whitelist()
	def get_subtree(self):
		"""Return the unit and all its descendants (for the map / OB tree)."""
		from evaluation.utils import get_descendants

		names = [self.name] + get_descendants("Force Arrangement", self.name)
		return frappe.get_all(
			"Force Arrangement",
			filters={"name": ("in", names)},
			fields=["name", "name_div", "size_div", "current_posture", "strength_pct",
					"combat_power_index", "latitude", "longitude", "lft", "rgt"],
			order_by="lft asc",
		)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def validate_force(doc, method=None):
	if not cstr_clean(doc.name_div):
		frappe.throw(_("Observed Unit Name is required"))

	if doc.parent_force_arrangement == doc.name:
		frappe.throw(_("A unit cannot be its own parent"))

	if doc.parent_force_arrangement:
		parent = frappe.db.get_value(
			"Force Arrangement", doc.parent_force_arrangement, ["evaluation_unit", "is_group"],
			as_dict=True,
		)
		if parent:
			if not doc.evaluation_unit:
				doc.evaluation_unit = parent.evaluation_unit
			elif parent.evaluation_unit and doc.evaluation_unit != parent.evaluation_unit:
				frappe.throw(
					_("Sub-units must belong to the same Evaluation Unit as their parent ({0})").format(
						parent.evaluation_unit
					)
				)
			if not cint(parent.is_group):
				frappe.db.set_value(
					"Force Arrangement", doc.parent_force_arrangement, "is_group", 1,
					update_modified=False,
				)

	doc.strength_pct = clamp(flt(doc.strength_pct) or 100)
	doc.committed_pct = clamp(flt(doc.committed_pct))

	if doc.latitude and doc.longitude:
		if not (-90 <= flt(doc.latitude) <= 90):
			frappe.throw(_("Latitude must be between -90 and 90"))
		if not (-180 <= flt(doc.longitude) <= 180):
			frappe.throw(_("Longitude must be between -180 and 180"))

	if doc.date and getdate(doc.date) > getdate(nowdate()):
		frappe.throw(_("Observation date cannot be in the future"))

	if not doc.date:
		doc.date = nowdate()

	# a unit with children must be a group
	if doc.is_new() is False and doc.is_group == 0:
		has_children = frappe.db.exists(
			"Force Arrangement", {"parent_force_arrangement": doc.name}
		)
		if has_children:
			doc.is_group = 1


def cstr_clean(value) -> str:
	return (value or "").strip()


def propagate_evaluation_unit(doc):
	"""Push the evaluation unit down to every descendant that has none."""
	if not doc.evaluation_unit:
		return
	from evaluation.utils import get_descendants

	for name in get_descendants("Force Arrangement", doc.name):
		current = frappe.db.get_value("Force Arrangement", name, "evaluation_unit")
		if not current:
			frappe.db.set_value("Force Arrangement", name, "evaluation_unit",
								doc.evaluation_unit, update_modified=False)


# ---------------------------------------------------------------------------
# Combat power index
# ---------------------------------------------------------------------------
def get_weights() -> dict[str, float]:
	weights = frappe.get_all("Combat Power Weight", fields=["factor", "weight"])
	out = {w.factor: flt(w.weight) for w in weights if w.factor}
	return out or dict(DEFAULT_WEIGHTS)


def compute_combat_power(doc) -> float:
	"""Weighted 0-100 index built from the four combat power pillars."""
	weights = get_weights()

	# --- readiness: average of the realist readiness lines
	readiness = 0.0
	if doc.readiness_lines:
		values = [flt(r.realist) for r in doc.readiness_lines if flt(r.realist) > 0]
		if values:
			readiness = sum(values) / len(values)
	if not readiness:
		readiness = flt(doc.strength_pct) or 0

	# --- logistics: percentage of supply lines that are not red
	logistics = 100.0
	if doc.logistics_lines:
		healthy = sum(1 for r in doc.logistics_lines if (r.status or "Green") != "Red")
		logistics = healthy * 100.0 / len(doc.logistics_lines)

	# --- ammunition: average days of supply mapped to 0-100 (30 days = 100)
	ammunition = 100.0
	if doc.ammunition_lines:
		dos = [flt(r.days_of_supply) for r in doc.ammunition_lines]
		ammunition = clamp(sum(dos) / len(dos) / 30.0 * 100 if dos else 100)

	# --- strength
	strength = clamp(flt(doc.strength_pct) or 0)

	pairs = [
		(clamp(readiness), weights.get("readiness", 0.35)),
		(clamp(logistics), weights.get("logistics", 0.25)),
		(clamp(ammunition), weights.get("ammunition", 0.20)),
		(clamp(strength), weights.get("strength", 0.20)),
	]
	return weighted_average(pairs)


@frappe.whitelist()
def recompute_all_indexes(evaluation_unit: str | None = None):
	"""Bulk refresh used after a weight change or a data import."""
	filters = {"is_group": 0}
	if evaluation_unit:
		filters["evaluation_unit"] = evaluation_unit

	updated = 0
	for name in frappe.get_all("Force Arrangement", filters=filters, pluck="name", limit_page_length=0):
		doc = frappe.get_doc("Force Arrangement", name)
		index = compute_combat_power(doc)
		if flt(doc.combat_power_index) != index:
			frappe.db.set_value("Force Arrangement", name, "combat_power_index", index,
								update_modified=False)
			updated += 1
	frappe.db.commit()
	return updated
