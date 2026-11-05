# Copyright (c) 2026, Aljahmi and contributors
# For license information, please see license.txt
"""Realistic demo data for the Evaluation app.

``create_demo_data()`` builds a small but coherent battlefield picture so the
workspaces, dashboards and reports show meaningful numbers on a fresh install:

    Evaluation Unit tree
      └── Northern Directorate
            └── Alpha Sector
    Force Arrangement tree (enemy units) with posture, readiness, logistics
    Daily observations that generate intel reports and targets
    Targets with CARVER analysis and BDA
    Operation order, situation report, threat assessment, casualty report
    Score cards for the observed units

Everything created is tagged with ``demo_data = 1`` (via a comment) and the
names are recorded in :data:`CREATED` so ``delete_demo_data()`` can undo it.
"""

from __future__ import annotations

import frappe
from frappe.utils import add_days, add_to_date, flt, now_datetime, nowdate

CREATED: dict[str, list[str]] = {}

UNITS = [
	{"unit_name": "Northern Directorate", "abbreviation": "ND", "is_group": 1},
	{"unit_name": "Alpha Sector", "abbreviation": "AS", "parent_evaluation_unit": "Northern Directorate"},
	{"unit_name": "Bravo Sector", "abbreviation": "BS", "parent_evaluation_unit": "Northern Directorate"},
]

FORCES = [
	{
		"name_div": "3rd Armoured Brigade", "size_div": "Brigade", "type": "Armoured",
		"parent": None, "posture": "Defend", "strength": 86,
		"readiness": 78, "logistics": 72, "ammo_days": 9,
	},
	{
		"name_div": "12th Mechanized Battalion", "size_div": "Battalion", "type": "Mechanized Infantry",
		"parent": "3rd Armoured Brigade", "posture": "Defend", "strength": 81,
		"readiness": 74, "logistics": 66, "ammo_days": 7,
	},
	{
		"name_div": "5th Artillery Regiment", "size_div": "Regiment", "type": "Artillery",
		"parent": "3rd Armoured Brigade", "posture": "Reserve", "strength": 92,
		"readiness": 88, "logistics": 80, "ammo_days": 14,
	},
	{
		"name_div": "9th Infantry Battalion", "size_div": "Battalion", "type": "Infantry",
		"parent": None, "posture": "Ambush", "strength": 68,
		"readiness": 61, "logistics": 55, "ammo_days": 4,
	},
	{
		"name_div": "2nd Recon Company", "size_div": "Company", "type": "Reconnaissance",
		"parent": None, "posture": "Screen", "strength": 95,
		"readiness": 91, "logistics": 88, "ammo_days": 12,
	},
]


def _record(doctype: str, name: str):
	CREATED.setdefault(doctype, []).append(name)


def _exists(doctype: str, name: str) -> bool:
	return bool(frappe.db.exists(doctype, name))


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------
def _create_units():
	for unit in UNITS:
		if _exists("Evaluation Unit", unit["unit_name"]):
			continue
		doc = frappe.get_doc({"doctype": "Evaluation Unit", **unit})
		doc.flags.ignore_permissions = True
		doc.insert()
		_record("Evaluation Unit", doc.name)


def _create_forces():
	for spec in FORCES:
		if _exists("Force Arrangement", spec["name_div"]):
			continue
		doc = frappe.get_doc(
			{
				"doctype": "Force Arrangement",
				"name_div": spec["name_div"],
				"size_div": spec["size_div"],
				"type_div": [{"type_div_name": spec["type"]}],
				"parent_force_arrangement": spec["parent"],
				"evaluation_unit": "Northern Directorate",
				"strength_pct": spec["strength"],
				"current_posture": spec["posture"],
				"date": nowdate(),
				"observation_confidence": "Probable",
			}
		)
		doc.append(
			"readiness_lines",
			{
				"readiness_metric": "Personnel Strength",
				"item_name": "Manning level",
				"item_group": "Personnel",
				"typical": 100,
				"realist": spec["readiness"],
			},
		)
		doc.append(
			"readiness_lines",
			{
				"readiness_metric": "Equipment Serviceability",
				"item_name": "Vehicle serviceability",
				"item_group": "Equipment",
				"typical": 100,
				"realist": spec["readiness"] - 5,
			},
		)
		doc.append(
			"logistics_lines",
			{
				"supply_class": "Class V - Ammunition",
				"on_hand": spec["logistics"] * 4,
				"critical_level": 150,
				"days_of_supply": spec["ammo_days"],
				"status": "Green" if spec["ammo_days"] > 8 else
						  "Yellow" if spec["ammo_days"] > 4 else "Red",
			},
		)
		doc.append(
			"logistics_lines",
			{
				"supply_class": "Class III - POL (Fuel & Lubricants)",
				"on_hand": spec["logistics"] * 3,
				"critical_level": 100,
				"days_of_supply": spec["ammo_days"] + 2,
				"status": "Green" if spec["ammo_days"] > 6 else "Yellow",
			},
		)
		doc.append(
			"ammunition_lines",
			{
				"fire_support_unit_type": "Artillery 155mm",
				"on_hand": spec["ammo_days"] * 40,
				"daily_consumption": 40,
				"critical_level": 120,
				"days_of_supply": spec["ammo_days"],
			},
		)
		doc.append(
			"fire_support_units",
			{
				"unit_name": f"{spec['name_div']} fires",
				"fire_support_unit_type": "Artillery 155mm",
				"number": 6,
				"standby_type": "Self-Propelled Guns",
			},
		)
		doc.flags.ignore_permissions = True
		doc.insert()
		_record("Force Arrangement", doc.name)


def _create_enemy_ob():
	root = "Northern Corps (Enemy)"
	if not _exists("Enemy Order of Battle", root):
		doc = frappe.get_doc(
			{
				"doctype": "Enemy Order of Battle",
				"unit_name": root,
				"unit_type": "Corps",
				"estimated_strength": 24000,
				"confidence_level": "Probable",
				"evaluation_unit": "Northern Directorate",
				"is_group": 1,
			}
		)
		doc.flags.ignore_permissions = True
		doc.insert()
		_record("Enemy Order of Battle", doc.name)

	for name, unit_type, strength in (
		("11th Infantry Division", "Division", 9000),
		("4th Armoured Division", "Division", 7500),
	):
		if _exists("Enemy Order of Battle", name):
			continue
		doc = frappe.get_doc(
			{
				"doctype": "Enemy Order of Battle",
				"unit_name": name,
				"unit_type": unit_type,
				"estimated_strength": strength,
				"confidence_level": "Confirmed",
				"parent_enemy_ob": root,
				"evaluation_unit": "Northern Directorate",
			}
		)
		doc.flags.ignore_permissions = True
		doc.insert()
		_record("Enemy Order of Battle", doc.name)


def _ensure_activity_side():
	if _exists("Activity Side", "Ground Recon"):
		return "Ground Recon"
	doc = frappe.get_doc({"doctype": "Activity Side", "side_name": "Ground Recon"})
	doc.flags.ignore_permissions = True
	doc.insert()
	_record("Activity Side", doc.name)
	return doc.name


def _create_observations():
	side = _ensure_activity_side()
	topics = [
		("Convoy of 12 BMPs moving north on HWY 5", "3rd Armoured Brigade", 0),
		("Digging in around grid 38S MB 4521 7834", "9th Infantry Battalion", 0),
		("Artillery pieces repositioned to ridge line", "5th Artillery Regiment", 1),
		("Recon patrol spotted near the river crossing", "2nd Recon Company", 0),
		("Fuel bowsers resupplying forward elements", "12th Mechanized Battalion", 1),
	]
	for offset, (topic, unit, gen_target) in enumerate(topics):
		existing = frappe.db.exists(
			"Daily Activities", {"the_topic": topic, "docstatus": ("<", 2)}
		)
		if existing:
			continue
		doc = frappe.get_doc(
			{
				"doctype": "Daily Activities",
				"naming_series": "DA-ACTIV.-.#####",
				"activity_side": side,
				"military_division": unit,
				"the_topic": topic,
				"start_of_event": add_days(nowdate(), -offset),
				"evaluation_unit": "Northern Directorate",
				"generates_intel": 1,
				"generates_target": gen_target,
				"text_summary": f"Field observation recorded by patrol on {add_days(nowdate(), -offset)}.",
			}
		)
		doc.flags.ignore_permissions = True
		doc.insert()
		doc.submit()
		_record("Daily Activities", doc.name)


def _create_targets():
	targets = [
		{
			"target_name": "Ammunition Depot Alpha",
			"target_type": "Ammunition Depot",
			"priority": "Critical",
			"confidence": "Confirmed",
			"unit": "5th Artillery Regiment",
			"carver": [5, 4, 3, 5, 5, 4],
		},
		{
			"target_name": "Command Post Bravo",
			"target_type": "Command Post",
			"priority": "High",
			"confidence": "Probable",
			"unit": "3rd Armoured Brigade",
			"carver": [5, 3, 4, 4, 4, 3],
		},
		{
			"target_name": "Bridge at KM 42",
			"target_type": "Bridge",
			"priority": "Medium",
			"confidence": "Probable",
			"unit": "9th Infantry Battalion",
			"carver": [3, 5, 2, 3, 4, 5],
		},
	]
	criteria = ["Criticality", "Accessibility", "Recuperability",
				"Vulnerability", "Effect", "Recognizability"]
	for spec in targets:
		if frappe.db.exists("Target", {"target_name": spec["target_name"], "docstatus": ("<", 2)}):
			continue
		doc = frappe.get_doc(
			{
				"doctype": "Target",
				"target_name": spec["target_name"],
				"target_type": spec["target_type"],
				"priority": spec["priority"],
				"confidence": spec["confidence"],
				"assigned_unit": spec["unit"],
				"evaluation_unit": "Northern Directorate",
				"latitude": 15.35,
				"longitude": 44.21,
				"valid_from": now_datetime(),
				"valid_until": add_to_date(now_datetime(), days=7),
			}
		)
		for criterion, score in zip(criteria, spec["carver"]):
			doc.append("carver_lines", {"criterion": criterion, "score": score})
		doc.flags.ignore_permissions = True
		doc.insert()
		_record("Target", doc.name)


def _create_operations():
	if not frappe.db.exists("Operation Order", {"operation_name": "Northern Shield", "docstatus": ("<", 2)}):
		doc = frappe.get_doc(
			{
				"doctype": "Operation Order",
				"naming_series": "OPORD-.YYYY.#####",
				"operation_name": "Northern Shield",
				"operation_type": "Defensive",
				"commanding_unit": "3rd Armoured Brigade",
				"start_datetime": now_datetime(),
				"status": "Active",
				"evaluation_unit": "Northern Directorate",
				"objective": "Hold the northern approach and deny the river crossing.",
				"concept_of_ops": "Two battalions forward, one in reserve, artillery in support.",
			}
		)
		doc.append("phases", {"phase_name": "Phase 1 - Prepare", "phase_order": 1})
		doc.append("phases", {"phase_name": "Phase 2 - Defend", "phase_order": 2})
		doc.append(
			"tasks",
			{
				"task_code": "T1",
				"task_description": "Occupy defensive positions along the ridge",
				"assigned_unit": "12th Mechanized Battalion",
				"task_type": "Secure",
				"priority": "High",
				"status": "In Progress",
				"progress": 45,
			},
		)
		doc.append(
			"tasks",
			{
				"task_code": "T2",
				"task_description": "Prepare counter-battery fire plan",
				"assigned_unit": "5th Artillery Regiment",
				"task_type": "Support",
				"priority": "Critical",
				"status": "Completed",
				"progress": 100,
			},
		)
		doc.append(
			"assigned_forces",
			{"force_arrangement": "3rd Armoured Brigade", "role": "Main", "commitment_pct": 80},
		)
		doc.flags.ignore_permissions = True
		doc.insert()
		_record("Operation Order", doc.name)

	if not frappe.db.exists("Situation Report", {"sector": "3rd Armoured Brigade", "docstatus": 1}):
		doc = frappe.get_doc(
			{
				"doctype": "Situation Report",
				"naming_series": "SITREP-.YYYY.#####",
				"report_datetime": now_datetime(),
				"sector": "3rd Armoured Brigade",
				"overall_status": "Limited Contact",
				"evaluation_unit": "Northern Directorate",
				"enemy_summary": "Enemy continues to reinforce the northern ridge.",
				"weather": "Clear, 24C, light wind from the north",
			}
		)
		doc.capture_snapshot()
		doc.flags.ignore_permissions = True
		doc.insert()
		doc.submit()
		_record("Situation Report", doc.name)

	if not frappe.db.exists("Threat Assessment", {"sector": "3rd Armoured Brigade"}):
		doc = frappe.get_doc(
			{
				"doctype": "Threat Assessment",
				"naming_series": "THR-.YYYY.#####",
				"sector": "3rd Armoured Brigade",
				"assessment_date": nowdate(),
				"evaluation_unit": "Northern Directorate",
			}
		)
		doc.append(
			"threat_lines",
			{"threat_factor": "Armoured counterattack", "capability": 4, "intent": 5,
			 "opportunity": 3, "affected_unit": "3rd Armoured Brigade"},
		)
		doc.append(
			"threat_lines",
			{"threat_factor": "Artillery suppression", "capability": 5, "intent": 3,
			 "opportunity": 4, "affected_unit": "9th Infantry Battalion"},
		)
		doc.flags.ignore_permissions = True
		doc.insert()
		_record("Threat Assessment", doc.name)

	if not frappe.db.exists("Casualty Report", {"force_arrangement": "9th Infantry Battalion"}):
		doc = frappe.get_doc(
			{
				"doctype": "Casualty Report",
				"naming_series": "CAS-.YYYY.#####",
				"report_datetime": now_datetime(),
				"force_arrangement": "9th Infantry Battalion",
				"evaluation_unit": "Northern Directorate",
				"notes": "Losses from artillery strike on forward position.",
			}
		)
		doc.append("personnel_lines", {"casualty_type": "KIA", "count": 7})
		doc.append("personnel_lines", {"casualty_type": "WIA", "count": 19})
		doc.append(
			"equipment_lines",
			{"readiness_metric": "Equipment Serviceability", "item_name": "BMP-2",
			 "quantity_lost": 3},
		)
		doc.flags.ignore_permissions = True
		doc.insert()
		doc.submit()
		_record("Casualty Report", doc.name)


def _create_score_cards():
	group = "Standard Unit Evaluation"
	if not _exists("Evaluation Criteria Group", group):
		return
	for unit in ("3rd Armoured Brigade", "9th Infantry Battalion"):
		if frappe.db.exists("Evaluation Score Card", {"force_arrangement": unit, "docstatus": ("<", 2)}):
			continue
		from evaluation.evaluation.doctype.evaluation_score_card.evaluation_score_card import (
			build_score_card,
		)

		name = build_score_card(
			"Force Arrangement", unit, group, "Northern Directorate", nowdate(), nowdate()
		)
		card = frappe.get_doc("Evaluation Score Card", name)
		score = 78 if "3rd" in unit else 64
		for line in card.score_lines:
			line.value = score
		card.flags.ignore_permissions = True
		card.save()
		_record("Evaluation Score Card", name)


def _create_personnel():
	people = [
		("Ahmed", "Saleh", "Al-Harbi", "Colonel", "Northern Directorate"),
		("Omar", "Khalid", "Al-Sanaani", "Major", "Alpha Sector"),
		("Yousef", "Ali", "Al-Qadhi", "Captain", "Bravo Sector"),
	]
	for first, middle, last, rank, unit in people:
		if frappe.db.exists("Personality", {"first_name": first, "last_name": last}):
			continue
		doc = frappe.get_doc(
			{
				"doctype": "Personality",
				"first_name": first,
				"middle_name": middle,
				"last_name": last,
				"status": "Active",
				"evaluation_unit": unit,
				"rank_name": rank,
			}
		)
		doc.flags.ignore_permissions = True
		doc.insert()
		_record("Personality", doc.name)


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------
def create_demo_data() -> dict:
	"""Create the demo dataset and return the record counts."""
	steps = [
		("units", _create_units),
		("forces", _create_forces),
		("enemy_ob", _create_enemy_ob),
		("observations", _create_observations),
		("targets", _create_targets),
		("operations", _create_operations),
		("score_cards", _create_score_cards),
		("personnel", _create_personnel),
	]
	done = {}
	for name, fn in steps:
		try:
			fn()
			frappe.db.commit()
			done[name] = "ok"
		except Exception as exc:  # noqa: BLE001
			frappe.db.rollback()
			done[name] = f"{type(exc).__name__}: {exc}"
			frappe.log_error(title=f"Evaluation demo data: {name}", message=frappe.get_traceback())
	return {"steps": done, "created": {k: len(v) for k, v in CREATED.items()}}


def delete_demo_data() -> dict:
	"""Delete everything created by :func:`create_demo_data`."""
	deleted = {}
	for doctype, names in CREATED.items():
		count = 0
		for name in names:
			if not frappe.db.exists(doctype, name):
				continue
			try:
				frappe.delete_doc(doctype, name, force=1, ignore_permissions=True)
				count += 1
			except Exception:  # noqa: BLE001
				pass
		deleted[doctype] = count
	frappe.db.commit()
	CREATED.clear()
	return deleted
