# Copyright (c) 2026, Aljahmi and contributors
# For license information, please see license.txt
"""Programmatic builders for the desk surfaces of the Evaluation app.

The app ships six workspaces (one per module) plus dashboards, number cards,
charts, reports, notifications and print formats.  Building them from Python
keeps the JSON out of the repo and makes the whole desk experience reproducible
on a fresh install.

Every builder is idempotent: running ``bench execute
evaluation.workspace_builder.build_workspaces`` twice will not duplicate rows.
"""

from __future__ import annotations

import json

import frappe
from frappe import _


def _exists(doctype: str, name: str) -> bool:
	return bool(frappe.db.exists(doctype, name))


def _upsert(doctype: str, name: str, values: dict):
	"""Create or update a standard document by name."""
	if _exists(doctype, name):
		doc = frappe.get_doc(doctype, name)
		doc.update(values)
		doc.flags.ignore_permissions = True
		doc.flags.ignore_links = True
		doc.save(ignore_permissions=True)
		return doc
	doc = frappe.get_doc({"doctype": doctype, "name": name, **values})
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True, ignore_if_duplicate=True)
	return doc


# ---------------------------------------------------------------------------
# Workspace definition
# ---------------------------------------------------------------------------
def _link(label, doctype, link_type="DocType", **kw):
	return {
		"type": "Link",
		"label": label,
		"link_type": link_type,
		"link_to": doctype,
		"hidden": 0,
		"onboard": 0,
		"is_query_report": 0,
		"dependencies": "",
		"link_count": 0,
		**kw,
	}


def _card(label):
	return {"type": "Card Break", "label": label, "hidden": 0, "onboard": 0,
			"is_query_report": 0, "link_count": 0, "dependencies": ""}


def _shortcut(label, link_to, link_type="DocType", doc_type="", color="Blue", stats_filter=None):
	return {
		"label": label,
		"link_to": link_to,
		"link_type": link_type,
		"type": "URL" if link_type == "URL" else link_type,
		"doc_type": doc_type,
		"color": color,
		"stats_filter": json.dumps(stats_filter) if stats_filter else "",
	}


def _content(blocks):
	"""Build the workspace grid content list from ``(type, name, col)`` tuples."""
	out = []
	for idx, (btype, name, col) in enumerate(blocks):
		entry = {"id": f"blk{idx:03d}", "type": btype, "data": {"col": col}}
		if btype == "shortcut":
			entry["data"]["shortcut_name"] = name
		elif btype in ("card", "chart", "number_card"):
			entry["data"][btype + "_name"] = name
		elif btype == "header":
			entry["data"]["text"] = f'<span class="h4"><b>{name}</b></span>'
		out.append(entry)
	return json.dumps(out)


WORKSPACE_SPECS = [
	{
		"label": "Evaluation",
		"title": "Evaluation",
		"module": "Evaluation",
		"icon": "evaluation",
		"indicator_color": "blue",
		"sequence_id": 1.0,
		"shortcuts": [
			_shortcut("Evaluation Unit", "Evaluation Unit", color="Blue",
					  stats_filter={"is_group": 0}),
			_shortcut("Score Card", "Evaluation Score Card", color="Green"),
			_shortcut("Criteria", "Evaluation Criteria", color="Orange"),
			_shortcut("Readiness", "Readiness Metric", color="Purple"),
		],
		"cards": [
			("Evaluation Setup", [
				("Evaluation Unit", "DocType"),
				("Evaluation Criteria", "DocType"),
				("Evaluation Criteria Group", "DocType"),
				("Combat Power Weight", "DocType"),
				("Readiness Metric", "DocType"),
				("Combat Effectiveness Type", "DocType"),
			]),
			("Scoring & Ranking", [
				("Evaluation Score Card", "DocType"),
				("Unit Ranking", "Report"),
				("Combat Power Index", "Report"),
			]),
			("Reference Tables", [
				("Evaluation Branch", "DocType"),
				("Evaluation Designation", "DocType"),
				("Evaluation Salutation", "DocType"),
				("Military Rank", "DocType"),
				("Combat Posture", "DocType"),
			]),
		],
		"charts": [
			{
				"chart_name": "Evaluation Score Trend",
				"chart_type": "Sum",
				"document_type": "Evaluation Score Card",
				"based_on": "period_to",
				"value_based_on": "total_score",
				"timespan": "Last Year",
				"time_interval": "Monthly",
				"type": "Line",
				"color": "#2490ef",
			},
			{
				"chart_name": "Score Cards by Unit",
				"chart_type": "Group By",
				"document_type": "Evaluation Score Card",
				"group_by_based_on": "evaluation_unit",
				"group_by_type": "Count",
				"type": "Donut",
				"number_of_groups": 10,
				"color": "#29cd42",
			},
		],
		"number_cards": [
			{
				"label": "Evaluation Units",
				"document_type": "Evaluation Unit",
				"function": "Count",
				"aggregate_function_based_on": "",
				"filters_json": json.dumps([["Evaluation Unit", "is_group", "=", 0]]),
			},
			{
				"label": "Score Cards",
				"document_type": "Evaluation Score Card",
				"function": "Count",
				"filters_json": json.dumps([["Evaluation Score Card", "docstatus", "=", 1]]),
			},
			{
				"label": "Average Score",
				"document_type": "Evaluation Score Card",
				"function": "Average",
				"aggregate_function_based_on": "total_score",
				"filters_json": json.dumps([["Evaluation Score Card", "docstatus", "=", 1]]),
			},
			{
				"label": "Active Criteria",
				"document_type": "Evaluation Criteria",
				"function": "Count",
				"filters_json": json.dumps([["Evaluation Criteria", "is_active", "=", 1]]),
			},
		],
	},
	{
		"label": "Reconnaissance",
		"title": "Reconnaissance",
		"module": "Reconnaissance",
		"icon": "search",
		"indicator_color": "orange",
		"sequence_id": 2.0,
		"shortcuts": [
			_shortcut("Daily Activity", "Daily Activities", color="Blue"),
			_shortcut("Observed Unit", "Force Arrangement", color="Red"),
			_shortcut("Activity Side", "Activity Side", color="Green"),
			_shortcut("Governorate", "Governorate", color="Purple"),
		],
		"cards": [
			("Daily Collection", [
				("Daily Activities", "DocType"),
				("Activity Worker", "DocType"),
				("Activity Reporter", "DocType"),
				("Public Activity", "DocType"),
				("Activity Side", "DocType"),
			]),
			("Geography", [
				("Governorate", "DocType"),
				("Governorate Directorate", "DocType"),
				("Insulation", "DocType"),
				("Geolocation", "DocType"),
				("Geographic Spread", "DocType"),
				("Tactic spread", "DocType"),
				("Management spread", "DocType"),
				("Movement Method", "DocType"),
			]),
			("Analysis", [
				("Observation Coverage", "Report"),
			]),
		],
		"charts": [
			{
				"chart_name": "Observation Trend",
				"chart_type": "Count",
				"document_type": "Daily Activities",
				"based_on": "start_of_event",
				"timespan": "Last Quarter",
				"time_interval": "Weekly",
				"type": "Line",
				"color": "#ff8f00",
			},
			{
				"chart_name": "Activities by Side",
				"chart_type": "Group By",
				"document_type": "Daily Activities",
				"group_by_based_on": "activity_side",
				"group_by_type": "Count",
				"type": "Bar",
				"number_of_groups": 10,
				"color": "#7b1fa2",
			},
		],
		"number_cards": [
			{
				"label": "Observations Today",
				"document_type": "Daily Activities",
				"function": "Count",
				"filters_json": json.dumps(
					[["Daily Activities", "start_of_event", "=", "Today"], ["Daily Activities", "docstatus", "=", 1]]
				),
			},
			{
				"label": "Units Under Observation",
				"document_type": "Force Arrangement",
				"function": "Count",
				"filters_json": json.dumps([["Force Arrangement", "is_group", "=", 0]]),
			},
			{
				"label": "Active Observers",
				"document_type": "Activity Worker",
				"function": "Count",
				"filters_json": "[]",
			},
		],
	},
	{
		"label": "Order Of Battle",
		"title": "Order Of Battle",
		"module": "Order Of Battle",
		"icon": "organization",
		"indicator_color": "red",
		"sequence_id": 3.0,
		"shortcuts": [
			_shortcut("Enemy OB", "Enemy Order of Battle", color="Red"),
			_shortcut("Force Arrangement", "Force Arrangement", color="Blue"),
			_shortcut("Logistics", "Logistics Line", color="Green"),
			_shortcut("Fire Support", "Fire Support Unit", color="Orange"),
		],
		"cards": [
			("Order of Battle", [
				("Enemy Order of Battle", "DocType"),
				("Force Arrangement", "DocType"),
				("Military Divisions", "DocType"),
				("Division Size", "DocType"),
				("Division Type", "DocType"),
				("Combat Posture", "DocType"),
			]),
			("Combat Elements", [
				("Fire Support Unit", "DocType"),
				("Fire Support Unit Type", "DocType"),
				("Engagement Force", "DocType"),
				("Reinforcement Force", "DocType"),
				("Training", "DocType"),
			]),
			("Sustainment", [
				("Supply Class", "DocType"),
				("Logistics Line", "DocType"),
				("Ammunition Line", "DocType"),
				("Readiness Line", "DocType"),
				("Combat Effectiveness Line", "DocType"),
			]),
			("Analysis", [
				("Order of Battle Summary", "Report"),
				("Force Comparison", "Report"),
				("Logistics Readiness", "Report"),
			]),
		],
		"charts": [
			{
				"chart_name": "Strength Distribution",
				"chart_type": "Group By",
				"document_type": "Force Arrangement",
				"group_by_based_on": "size_div",
				"group_by_type": "Count",
				"type": "Bar",
				"number_of_groups": 12,
				"color": "#e64a19",
			},
			{
				"chart_name": "Posture Breakdown",
				"chart_type": "Group By",
				"document_type": "Force Arrangement",
				"group_by_based_on": "current_posture",
				"group_by_type": "Count",
				"type": "Donut",
				"number_of_groups": 10,
				"color": "#546e7a",
			},
		],
		"number_cards": [
			{
				"label": "Observed Units",
				"document_type": "Force Arrangement",
				"function": "Count",
				"filters_json": json.dumps([["Force Arrangement", "is_group", "=", 0]]),
			},
			{
				"label": "OB Nodes",
				"document_type": "Enemy Order of Battle",
				"function": "Count",
				"filters_json": "[]",
			},
			{
				"label": "Avg Strength",
				"document_type": "Force Arrangement",
				"function": "Average",
				"aggregate_function_based_on": "strength_pct",
				"filters_json": "[]",
			},
		],
	},
	{
		"label": "Targeting",
		"title": "Targeting",
		"module": "Targeting",
		"icon": "target",
		"indicator_color": "green",
		"sequence_id": 4.0,
		"shortcuts": [
			_shortcut("Target", "Target", color="Red"),
			_shortcut("Target Category", "Target Category", color="Blue"),
			_shortcut("Target Type", "Target Type", color="Green"),
			_shortcut("BDA Register", "BDA Register", link_type="Report", color="Orange"),
		],
		"cards": [
			("Target Library", [
				("Target", "DocType"),
				("Target Category", "DocType"),
				("Target Type", "DocType"),
			]),
			("Analysis", [
				("CARVER Matrix", "Report"),
				("BDA Register", "Report"),
			]),
		],
		"charts": [
			{
				"chart_name": "Targets by Priority",
				"chart_type": "Group By",
				"document_type": "Target",
				"group_by_based_on": "priority",
				"group_by_type": "Count",
				"type": "Donut",
				"number_of_groups": 4,
				"color": "#43a047",
			},
			{
				"chart_name": "Target Status Funnel",
				"chart_type": "Group By",
				"document_type": "Target",
				"group_by_based_on": "status",
				"group_by_type": "Count",
				"type": "Bar",
				"number_of_groups": 10,
				"color": "#00897b",
			},
		],
		"number_cards": [
			{
				"label": "Active Targets",
				"document_type": "Target",
				"function": "Count",
				"filters_json": json.dumps([["Target", "status", "=", "Active"]]),
			},
			{
				"label": "Time Sensitive",
				"document_type": "Target",
				"function": "Count",
				"filters_json": json.dumps([["Target", "priority", "in", ["Critical", "High"]]]),
			},
			{
				"label": "No Strike",
				"document_type": "Target",
				"function": "Count",
				"filters_json": json.dumps([["Target", "no_strike", "=", 1]]),
			},
		],
	},
	{
		"label": "Operations",
		"title": "Operations",
		"module": "Operations",
		"icon": "milestone",
		"indicator_color": "purple",
		"sequence_id": 5.0,
		"shortcuts": [
			_shortcut("Operation Order", "Operation Order", color="Blue"),
			_shortcut("Intel Report", "Intel Report", color="Red"),
			_shortcut("Situation Report", "Situation Report", color="Orange"),
			_shortcut("Threat Assessment", "Threat Assessment", color="Purple"),
		],
		"cards": [
			("Planning", [
				("Operation Order", "DocType"),
				("Operation Phase", "DocType"),
				("Operation Task", "DocType"),
				("Operation Force Assignment", "DocType"),
				("Operation Target Link", "DocType"),
			]),
			("Intelligence", [
				("Intel Report", "DocType"),
				("Threat Assessment", "DocType"),
				("Situation Report", "DocType"),
				("Situation Layer", "DocType"),
				("Situation Snapshot Line", "DocType"),
			]),
			("Battle Damage", [
				("Casualty Report", "DocType"),
				("Casualty Personnel Line", "DocType"),
				("Casualty Equipment Line", "DocType"),
			]),
			("Analysis", [
				("Intel Source Reliability", "Report"),
				("Situation Overview", "Report"),
			]),
		],
		"charts": [
			{
				"chart_name": "Intel by Source",
				"chart_type": "Group By",
				"document_type": "Intel Report",
				"group_by_based_on": "source_type",
				"group_by_type": "Count",
				"type": "Donut",
				"number_of_groups": 6,
				"color": "#6d4c41",
			},
			{
				"chart_name": "Threat Level Trend",
				"chart_type": "Group By",
				"document_type": "Threat Assessment",
				"group_by_based_on": "overall_threat_level",
				"group_by_type": "Count",
				"type": "Bar",
				"number_of_groups": 4,
				"color": "#c62828",
			},
		],
		"number_cards": [
			{
				"label": "Open Intel",
				"document_type": "Intel Report",
				"function": "Count",
				"filters_json": json.dumps([["Intel Report", "docstatus", "=", 0]]),
			},
			{
				"label": "Operations Running",
				"document_type": "Operation Order",
				"function": "Count",
				"filters_json": json.dumps([["Operation Order", "status", "=", "Active"]]),
			},
			{
				"label": "Situation Reports",
				"document_type": "Situation Report",
				"function": "Count",
				"filters_json": json.dumps([["Situation Report", "docstatus", "=", 1]]),
			},
			{
				"label": "Critical Threats",
				"document_type": "Threat Assessment",
				"function": "Count",
				"filters_json": json.dumps(
					[["Threat Assessment", "overall_threat_level", "=", "Critical"]]
				),
			},
		],
	},
	{
		"label": "Personnel",
		"title": "Personnel",
		"module": "Personnel",
		"icon": "users",
		"indicator_color": "cyan",
		"sequence_id": 6.0,
		"shortcuts": [
			_shortcut("Personality", "Personality", color="Blue"),
			_shortcut("Military Rank", "Military Rank", color="Green"),
			_shortcut("Army Chief", "Army Chief", color="Orange"),
			_shortcut("Evaluation Branch", "Evaluation Branch", color="Purple"),
		],
		"cards": [
			("People", [
				("Personality", "DocType"),
				("Personality Dependent", "DocType"),
				("Army Chief", "DocType"),
			]),
			("Reference Tables", [
				("Military Rank", "DocType"),
				("Evaluation Branch", "DocType"),
				("Evaluation Designation", "DocType"),
				("Evaluation Salutation", "DocType"),
				("Gender", "DocType"),
			]),
			("Analysis", [
				("Personnel Roster", "Report"),
			]),
		],
		"charts": [
			{
				"chart_name": "Rank Distribution",
				"chart_type": "Group By",
				"document_type": "Personality",
				"group_by_based_on": "rank_name",
				"group_by_type": "Count",
				"type": "Bar",
				"number_of_groups": 15,
				"color": "#0097a7",
			},
		],
		"number_cards": [
			{
				"label": "Personnel",
				"document_type": "Personality",
				"function": "Count",
				"filters_json": "[]",
			},
			{
				"label": "Active",
				"document_type": "Personality",
				"function": "Count",
				"filters_json": json.dumps([["Personality", "status", "=", "Active"]]),
			},
		],
	},
]


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------
def build_workspaces():
	for spec in WORKSPACE_SPECS:
		_build_workspace(spec)
	frappe.db.commit()


def _build_workspace(spec: dict):
	name = spec["label"]
	if _exists("Workspace", name):
		frappe.delete_doc("Workspace", name, force=1, ignore_permissions=True)
		frappe.db.commit()

	links = []
	content_blocks = []

	# shortcuts row
	for sc in spec["shortcuts"]:
		label = sc["label"]
		links.append(
			{
				"type": "Link",
				"label": label,
				"link_type": sc["link_type"] if sc["link_type"] in ("DocType", "Page", "Report") else "DocType",
				"link_to": sc["link_to"],
				"doc_type": sc.get("doc_type") or "",
				"hidden": 0,
				"onboard": 0,
				"is_query_report": 1 if sc["link_type"] == "Report" else 0,
				"dependencies": "",
				"link_count": 0,
			}
		)
		content_blocks.append(("shortcut", label, 3))

	content_blocks.append(("spacer", None, 12))

	col = 4
	for card_label, card_links in spec["cards"]:
		links.append(
			{
				"type": "Card Break",
				"label": card_label,
				"hidden": 0,
				"onboard": 0,
				"is_query_report": 0,
				"dependencies": "",
				"link_count": len(card_links),
			}
		)
		content_blocks.append(("card", card_label, col))
		for link_label, link_type in card_links:
			links.append(
				{
					"type": "Link",
					"label": link_label,
					"link_type": link_type if link_type in ("DocType", "Page", "Report") else "DocType",
					"link_to": link_label,
					"doc_type": "",
					"hidden": 0,
					"onboard": 0,
					"is_query_report": 1 if link_type == "Report" else 0,
					"dependencies": "",
					"link_count": 0,
				}
			)
		col = 4 if col == 8 else col + 4

	if spec.get("charts"):
		content_blocks.append(("header", "Analysis", 12))
		for chart in spec["charts"]:
			content_blocks.append(("chart", chart["chart_name"], 6))
	if spec.get("number_cards"):
		content_blocks.append(("header", "Key Numbers", 12))
		for nc in spec["number_cards"]:
			content_blocks.append(("number_card", nc["label"], 3))

	doc = frappe.get_doc(
		{
			"doctype": "Workspace",
			"label": spec["label"],
			"title": spec["title"],
			"module": spec["module"],
			"icon": spec["icon"],
			"indicator_color": spec["indicator_color"],
			"sequence_id": spec["sequence_id"],
			"public": 1,
			"is_hidden": 0,
			"content": _content(content_blocks),
			"links": links,
			"charts": [{"chart_name": c["chart_name"], "label": c["chart_name"]} for c in spec.get("charts", [])],
			"number_cards": [
				{"number_card_name": nc["label"], "label": nc["label"]}
				for nc in spec.get("number_cards", [])
			],
			"roles": [],
		}
	)
	doc.flags.ignore_permissions = True
	doc.flags.ignore_links = True
	doc.insert(ignore_permissions=True, ignore_if_duplicate=True, set_name=name)
	return frappe.get_doc("Workspace", name)


# ---------------------------------------------------------------------------
# Charts, number cards and dashboards
# ---------------------------------------------------------------------------
def build_charts_and_cards():
	"""Create the Dashboard Chart / Number Card records referenced by workspaces."""
	seen_charts: set[str] = set()
	seen_cards: set[str] = set()

	for spec in WORKSPACE_SPECS:
		for chart in spec.get("charts", []):
			key = chart["chart_name"]
			if key in seen_charts:
				continue
			seen_charts.add(key)
			values = {
				"chart_name": key,
				"chart_type": chart["chart_type"],
				"document_type": chart["document_type"],
				"based_on": chart.get("based_on"),
				"value_based_on": chart.get("value_based_on"),
				"group_by_based_on": chart.get("group_by_based_on"),
				"group_by_type": chart.get("group_by_type", "Count"),
				"number_of_groups": chart.get("number_of_groups", 0),
				"type": chart["type"],
				"timespan": chart.get("timespan", "Last Year"),
				"time_interval": chart.get("time_interval", "Monthly"),
				"timeseries": 1 if chart.get("based_on") else 0,
				"is_public": 1,
				"is_standard": 1,
				"module": "Evaluation",
				"filters_json": "[]",
			}
			_save_doc("Dashboard Chart", key, values)

		for nc in spec.get("number_cards", []):
			key = nc["label"]
			if key in seen_cards:
				continue
			seen_cards.add(key)
			values = {
				"label": key,
				"document_type": nc["document_type"],
				"function": nc["function"],
				"aggregate_function_based_on": nc.get("aggregate_function_based_on") or "",
				"filters_json": nc.get("filters_json") or "[]",
				"is_public": 1,
				"is_standard": 1,
				"module": "Evaluation",
				"show_percentage_stats": 0,
			}
			_save_doc("Number Card", key, values)

	frappe.db.commit()


def _save_doc(doctype: str, name: str, values: dict):
	"""Create or update a named standard document, swallowing benign errors."""
	try:
		if frappe.db.exists(doctype, name):
			doc = frappe.get_doc(doctype, name)
			for field, value in values.items():
				doc.set(field, value)
			doc.flags.ignore_permissions = True
			doc.flags.ignore_links = True
			doc.save(ignore_permissions=True)
		else:
			frappe.get_doc({"doctype": doctype, "name": name, **values}).insert(
				ignore_permissions=True, ignore_if_duplicate=True, set_name=name
			)
	except Exception as exc:  # noqa: BLE001 - keep installing
		frappe.log_error(title=f"Evaluation: could not save {doctype} {name}", message=str(exc))


DASHBOARD_SPECS = [
	{
		"dashboard_name": "Recon Overview",
		"charts": ["Observation Trend", "Activities by Side", "Strength Distribution",
				   "Posture Breakdown"],
		"cards": ["Observations Today", "Units Under Observation", "Observed Units",
				  "Active Observers"],
	},
	{
		"dashboard_name": "Targeting Board",
		"charts": ["Targets by Priority", "Target Status Funnel", "Threat Level Trend"],
		"cards": ["Active Targets", "Time Sensitive", "Critical Threats"],
	},
	{
		"dashboard_name": "Evaluation Overview",
		"charts": ["Evaluation Score Trend", "Score Cards by Unit"],
		"cards": ["Evaluation Units", "Score Cards", "Average Score"],
	},
	{
		"dashboard_name": "Operations Overview",
		"charts": ["Intel by Source", "Threat Level Trend", "Observation Trend"],
		"cards": ["Open Intel", "Operations Running", "Situation Reports", "Critical Threats"],
	},
]


def build_dashboards():
	"""Create the standard dashboards used on the workspaces."""
	build_charts_and_cards()

	for spec in DASHBOARD_SPECS:
		name = spec["dashboard_name"]
		charts = [{"chart": c} for c in spec["charts"] if frappe.db.exists("Dashboard Chart", c)]
		cards = [{"card": c} for c in spec["cards"] if frappe.db.exists("Number Card", c)]
		values = {
			"dashboard_name": name,
			"module": "Evaluation",
			"is_standard": 1,
			"charts": charts,
			"cards": cards,
		}
		try:
			if frappe.db.exists("Dashboard", name):
				doc = frappe.get_doc("Dashboard", name)
				doc.update({"charts": charts, "cards": cards})
				doc.flags.ignore_permissions = True
				doc.save(ignore_permissions=True)
			else:
				doc = frappe.get_doc({"doctype": "Dashboard", **values})
				doc.flags.ignore_permissions = True
				doc.insert(ignore_permissions=True, ignore_if_duplicate=True, set_name=name)
		except Exception as exc:  # noqa: BLE001
			frappe.log_error(title=f"Evaluation: dashboard {name}", message=str(exc))

	frappe.db.commit()


def build_number_cards():
	"""Public helper kept for ``bench execute`` compatibility."""
	build_charts_and_cards()
