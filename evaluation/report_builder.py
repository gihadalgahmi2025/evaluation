# Copyright (c) 2026, Aljahmi and contributors
# For license information, please see license.txt
"""Report builder for the Evaluation app.

Every report is defined once as a :class:`ReportSpec` and materialised both as

* a **Query Report** record (so it shows up in the desk report list and can be
  exported to Excel/CSV), and
* a plain SQL query that can be executed directly.

The builder is idempotent - re-running it updates the existing report records.
"""

from __future__ import annotations

import frappe
from frappe import _

# ---------------------------------------------------------------------------
# Report specifications
# ---------------------------------------------------------------------------
REPORT_SPECS = [
	# ----------------------------------------------------------------- Evaluation
	{
		"report_name": "Unit Ranking",
		"module": "Evaluation",
		"ref_doctype": "Evaluation Score Card",
		"report_type": "Query Report",
		"query": """
			SELECT
				esc.evaluation_unit            AS `Evaluation Unit`,
				COUNT(*)                       AS `Cards`,
				ROUND(AVG(esc.total_score), 2) AS `Average Score`,
				MAX(esc.total_score)           AS `Best Score`,
				MIN(esc.total_score)           AS `Lowest Score`,
				MAX(esc.modified)              AS `Last Evaluated`
			FROM `tabEvaluation Score Card` esc
			WHERE esc.docstatus < 2
			  AND (%(evaluation_unit)s IS NULL OR esc.evaluation_unit = %(evaluation_unit)s)
			  AND (%(from_date)s IS NULL OR esc.period_to >= %(from_date)s)
			  AND (%(to_date)s IS NULL OR esc.period_from <= %(to_date)s)
			GROUP BY esc.evaluation_unit
			ORDER BY `Average Score` DESC
		""",
		"filters": [
			{"fieldname": "evaluation_unit", "label": "Evaluation Unit",
			 "fieldtype": "Link", "options": "Evaluation Unit"},
			{"fieldname": "from_date", "label": "From Date", "fieldtype": "Date"},
			{"fieldname": "to_date", "label": "To Date", "fieldtype": "Date"},
		],
		"columns": [],
	},
	{
		"report_name": "Combat Power Index",
		"module": "Evaluation",
		"ref_doctype": "Force Arrangement",
		"report_type": "Query Report",
		"query": """
			SELECT
				fa.name                        AS `Unit Code`,
				fa.name_div                    AS `Observed Unit`,
				fa.size_div                    AS `Echelon`,
				fa.current_posture             AS `Posture`,
				fa.strength_pct                AS `Strength Pct`,
				ROUND(AVG(CASE WHEN rl.readiness_metric IS NOT NULL
					  THEN rl.realist END), 2) AS `Readiness Pct`,
				ROUND(SUM(CASE WHEN ll.status = 'Red' THEN 1 ELSE 0 END), 0) AS `Red Supply Lines`,
				ROUND(SUM(CASE WHEN al.days_of_supply < 3 THEN 1 ELSE 0 END), 0) AS `Critical Ammo`,
				fa.modified                    AS `Last Updated`
			FROM `tabForce Arrangement` fa
			LEFT JOIN `tabReadiness Line` rl        ON rl.parent = fa.name
			LEFT JOIN `tabLogistics Line` ll        ON ll.parent = fa.name
			LEFT JOIN `tabAmmunition Line` al       ON al.parent = fa.name
			WHERE fa.is_group = 0
			  AND (%(evaluation_unit)s IS NULL OR fa.evaluation_unit = %(evaluation_unit)s)
			GROUP BY fa.name
			ORDER BY `Strength Pct` DESC
		""",
		"filters": [
			{"fieldname": "evaluation_unit", "label": "Evaluation Unit",
			 "fieldtype": "Link", "options": "Evaluation Unit"},
		],
		"columns": [],
	},
	{
		"report_name": "Criteria Weights",
		"module": "Evaluation",
		"ref_doctype": "Evaluation Criteria",
		"report_type": "Query Report",
		"query": """
			SELECT
				ec.applies_to                 AS `Applies To`,
				ec.criterion_name             AS `Criterion`,
				ec.criterion_type             AS `Type`,
				ec.weight                     AS `Weight`,
				ec.max_value                  AS `Max Value`,
				ROUND(ec.weight * 100 / SUM(ec.weight) OVER (PARTITION BY ec.applies_to), 2)
											  AS `Share Pct`,
				ec.is_active                  AS `Active`
			FROM `tabEvaluation Criteria` ec
			ORDER BY ec.applies_to, ec.weight DESC
		""",
		"filters": [],
		"columns": [],
	},
	# ------------------------------------------------------------- Reconnaissance
	{
		"report_name": "Observation Coverage",
		"module": "Reconnaissance",
		"ref_doctype": "Daily Activities",
		"report_type": "Query Report",
		"query": """
			SELECT
				da.activity_side               AS `Collection Side`,
				da.governorate_name            AS `Governorate`,
				COUNT(*)                       AS `Observations`,
				COUNT(DISTINCT da.military_division) AS `Distinct Units`,
				COUNT(DISTINCT da.activity_worker)   AS `Observers`,
				MIN(da.start_of_event)         AS `First Observation`,
				MAX(da.start_of_event)         AS `Last Observation`,
				SUM(CASE WHEN da.generates_target = 1 THEN 1 ELSE 0 END) AS `Target Nominations`,
				SUM(CASE WHEN da.generates_intel = 1 THEN 1 ELSE 0 END)  AS `Intel Produced`
			FROM `tabDaily Activities` da
			WHERE da.docstatus = 1
			  AND (%(from_date)s IS NULL OR da.start_of_event >= %(from_date)s)
			  AND (%(to_date)s IS NULL OR da.start_of_event <= %(to_date)s)
			  AND (%(evaluation_unit)s IS NULL OR da.evaluation_unit = %(evaluation_unit)s)
			GROUP BY da.activity_side, da.governorate_name
			ORDER BY `Observations` DESC
		""",
		"filters": [
			{"fieldname": "from_date", "label": "From Date", "fieldtype": "Date"},
			{"fieldname": "to_date", "label": "To Date", "fieldtype": "Date"},
			{"fieldname": "evaluation_unit", "label": "Evaluation Unit",
			 "fieldtype": "Link", "options": "Evaluation Unit"},
		],
		"columns": [],
	},
	{
		"report_name": "Observer Performance",
		"module": "Reconnaissance",
		"ref_doctype": "Daily Activities",
		"report_type": "Query Report",
		"query": """
			SELECT
				da.activity_worker             AS `Observer`,
				COUNT(*)                       AS `Total Observations`,
				SUM(CASE WHEN da.docstatus = 1 THEN 1 ELSE 0 END) AS `Submitted`,
				SUM(CASE WHEN da.generates_intel = 1 THEN 1 ELSE 0 END) AS `Intel Raised`,
				SUM(CASE WHEN da.generates_target = 1 THEN 1 ELSE 0 END) AS `Targets Raised`,
				COUNT(DISTINCT da.start_of_event) AS `Active Days`,
				MAX(da.start_of_event)         AS `Last Observation`
			FROM `tabDaily Activities` da
			WHERE IFNULL(da.activity_worker, '') != ''
			GROUP BY da.activity_worker
			ORDER BY `Total Observations` DESC
		""",
		"filters": [],
		"columns": [],
	},
	# ----------------------------------------------------------- Order of battle
	{
		"report_name": "Order of Battle Summary",
		"module": "Order Of Battle",
		"ref_doctype": "Force Arrangement",
		"report_type": "Query Report",
		"query": """
			SELECT
				fa.name_div                    AS `Observed Unit`,
				fa.size_div                    AS `Echelon`,
				fa.parent_force_arrangement    AS `Parent Unit`,
				fa.current_posture             AS `Posture`,
				fa.strength_pct                AS `Strength Pct`,
				fa.observation_confidence      AS `Confidence`,
				fa.date                        AS `Last Observation`,
				(SELECT COUNT(*) FROM `tabForce Arrangement` c
				  WHERE c.parent_force_arrangement = fa.name) AS `Sub Units`,
				(SELECT COUNT(*) FROM `tabFire Support Unit` f
				  WHERE f.parent = fa.name)      AS `Fire Support`,
				fa.last_daily_activity         AS `Last Activity`
			FROM `tabForce Arrangement` fa
			WHERE (%(evaluation_unit)s IS NULL OR fa.evaluation_unit = %(evaluation_unit)s)
			  AND (%(is_group)s = 1 OR fa.is_group = 0)
			ORDER BY fa.lft
		""",
		"filters": [
			{"fieldname": "evaluation_unit", "label": "Evaluation Unit",
			 "fieldtype": "Link", "options": "Evaluation Unit"},
			{"fieldname": "is_group", "label": "Include Groups", "fieldtype": "Check"},
		],
		"columns": [],
	},
	{
		"report_name": "Force Comparison",
		"module": "Order Of Battle",
		"ref_doctype": "Force Arrangement",
		"report_type": "Query Report",
		"query": """
			SELECT
				fa.name_div                    AS `Observed Unit`,
				fa.size_div                    AS `Echelon`,
				fa.current_posture             AS `Posture`,
				fa.strength_pct                AS `Strength Pct`,
				ROUND(AVG(rl.realist), 1)      AS `Readiness Pct`,
				ROUND(AVG(ce.value), 1)        AS `Combat Effectiveness`,
				COUNT(DISTINCT fu.name)        AS `Fire Support Assets`,
				COUNT(DISTINCT CASE WHEN al.days_of_supply < 3 THEN al.name END) AS `Ammo Critical`
			FROM `tabForce Arrangement` fa
			LEFT JOIN `tabReadiness Line` rl             ON rl.parent = fa.name
			LEFT JOIN `tabCombat Effectiveness Line` ce  ON ce.parent = fa.name
			LEFT JOIN `tabFire Support Unit` fu          ON fu.parent = fa.name
			LEFT JOIN `tabAmmunition Line` al            ON al.parent = fa.name
			WHERE fa.is_group = 0
			GROUP BY fa.name
			ORDER BY `Strength Pct` DESC
		""",
		"filters": [],
		"columns": [],
	},
	{
		"report_name": "Logistics Readiness",
		"module": "Order Of Battle",
		"ref_doctype": "Logistics Line",
		"report_type": "Query Report",
		"query": """
			SELECT
				ll.parent                      AS `Observed Unit`,
				sc.class_code                  AS `Class`,
				ll.supply_class                AS `Supply Class`,
				ll.on_hand                     AS `On Hand`,
				ll.critical_level              AS `Critical Level`,
				ll.days_of_supply              AS `Days of Supply`,
				ll.status                      AS `Status`,
				CASE
					WHEN ll.days_of_supply < 1 THEN 'Critical'
					WHEN ll.days_of_supply < 3 THEN 'Low'
					WHEN ll.days_of_supply < 7 THEN 'Adequate'
					ELSE 'Healthy'
				END                            AS `Assessment`
			FROM `tabLogistics Line` ll
			LEFT JOIN `tabSupply Class` sc ON sc.name = ll.supply_class
			WHERE (%(evaluation_unit)s IS NULL OR ll.parent IN (
					SELECT name FROM `tabForce Arrangement`
					 WHERE evaluation_unit = %(evaluation_unit)s))
			ORDER BY ll.days_of_supply ASC
		""",
		"filters": [
			{"fieldname": "evaluation_unit", "label": "Evaluation Unit",
			 "fieldtype": "Link", "options": "Evaluation Unit"},
		],
		"columns": [],
	},
	# ------------------------------------------------------------------ Targeting
	{
		"report_name": "CARVER Matrix",
		"module": "Targeting",
		"ref_doctype": "Target",
		"report_type": "Query Report",
		"query": """
			SELECT
				t.name                         AS `Target`,
				t.target_name                  AS `Target Name`,
				t.target_type                  AS `Type`,
				t.priority                     AS `Priority`,
				MAX(CASE WHEN cl.criterion = 'Criticality'     THEN cl.score END) AS `Criticality`,
				MAX(CASE WHEN cl.criterion = 'Accessibility'   THEN cl.score END) AS `Accessibility`,
				MAX(CASE WHEN cl.criterion = 'Recuperability'  THEN cl.score END) AS `Recuperability`,
				MAX(CASE WHEN cl.criterion = 'Vulnerability'   THEN cl.score END) AS `Vulnerability`,
				MAX(CASE WHEN cl.criterion = 'Effect'          THEN cl.score END) AS `Effect`,
				MAX(CASE WHEN cl.criterion = 'Recognizability' THEN cl.score END) AS `Recognizability`,
				ROUND(SUM(cl.score), 1)        AS `CARVER Total`
			FROM `tabTarget` t
			LEFT JOIN `tabTarget Carver Line` cl ON cl.parent = t.name
			WHERE t.docstatus < 2
			  AND (%(evaluation_unit)s IS NULL OR t.evaluation_unit = %(evaluation_unit)s)
			  AND (%(priority)s IS NULL OR t.priority = %(priority)s)
			GROUP BY t.name
			ORDER BY `CARVER Total` DESC
		""",
		"filters": [
			{"fieldname": "evaluation_unit", "label": "Evaluation Unit",
			 "fieldtype": "Link", "options": "Evaluation Unit"},
			{"fieldname": "priority", "label": "Priority", "fieldtype": "Select",
			 "options": "\nCritical\nHigh\nMedium\nLow"},
		],
		"columns": [],
	},
	{
		"report_name": "BDA Register",
		"module": "Targeting",
		"ref_doctype": "Target Bda Line",
		"report_type": "Query Report",
		"query": """
			SELECT
				bl.parent                      AS `Target`,
				t.target_name                  AS `Target Name`,
				bl.assessment_datetime         AS `Assessed On`,
				bl.damage_level                AS `Damage Level`,
				bl.assessed_by                 AS `Assessed By`,
				bl.restrike_needed             AS `Restrike Needed`,
				bl.linked_activity             AS `Supporting Observation`,
				bl.notes                       AS `Remarks`
			FROM `tabTarget Bda Line` bl
			LEFT JOIN `tabTarget` t ON t.name = bl.parent
			WHERE (%(from_date)s IS NULL OR DATE(bl.assessment_datetime) >= %(from_date)s)
			  AND (%(to_date)s IS NULL OR DATE(bl.assessment_datetime) <= %(to_date)s)
			ORDER BY bl.assessment_datetime DESC
		""",
		"filters": [
			{"fieldname": "from_date", "label": "From Date", "fieldtype": "Date"},
			{"fieldname": "to_date", "label": "To Date", "fieldtype": "Date"},
		],
		"columns": [],
	},
	{
		"report_name": "Target Priority Board",
		"module": "Targeting",
		"ref_doctype": "Target",
		"report_type": "Query Report",
		"query": """
			SELECT
				t.priority                     AS `Priority`,
				t.workflow_state               AS `Status`,
				COUNT(*)                       AS `Targets`,
				SUM(CASE WHEN t.no_strike = 1 THEN 1 ELSE 0 END) AS `No Strike`,
				SUM(CASE WHEN t.restrike_recommended = 1 THEN 1 ELSE 0 END) AS `Restrike`,
				ROUND(AVG(t.priority_score), 1) AS `Avg Score`
			FROM `tabTarget` t
			WHERE t.docstatus < 2
			GROUP BY t.priority, t.workflow_state
			ORDER BY FIELD(t.priority, 'Critical','High','Medium','Low'), t.workflow_state
		""",
		"filters": [],
		"columns": [],
	},
	# ----------------------------------------------------------------- Operations
	{
		"report_name": "Intel Source Reliability",
		"module": "Operations",
		"ref_doctype": "Intel Report",
		"report_type": "Query Report",
		"query": """
			SELECT
				ir.source_type                 AS `Source Type`,
				ir.reliability                 AS `Reliability`,
				ir.credibility                 AS `Credibility`,
				CONCAT(IFNULL(ir.reliability,'-'), IFNULL(ir.credibility,'-')) AS `NATO Rating`,
				COUNT(*)                       AS `Reports`,
				SUM(CASE WHEN ir.generates_target = 1 THEN 1 ELSE 0 END) AS `Targets Generated`,
				MAX(ir.report_datetime)        AS `Last Report`
			FROM `tabIntel Report` ir
			WHERE ir.docstatus < 2
			GROUP BY ir.source_type, ir.reliability, ir.credibility
			ORDER BY `Reports` DESC
		""",
		"filters": [],
		"columns": [],
	},
	{
		"report_name": "Situation Overview",
		"module": "Operations",
		"ref_doctype": "Situation Report",
		"report_type": "Query Report",
		"query": """
			SELECT
				sr.report_datetime             AS `Reported`,
				sr.sector                      AS `Sector`,
				sr.overall_status              AS `Status`,
				sr.evaluation_unit             AS `Unit`,
				COUNT(DISTINCT snl.force_arrangement) AS `Units Reported`,
				ROUND(AVG(snl.strength_pct), 1) AS `Avg Strength Pct`,
				COUNT(DISTINCT sal.daily_activity)    AS `Linked Activities`
			FROM `tabSituation Report` sr
			LEFT JOIN `tabSituation Snapshot Line` snl ON snl.parent = sr.name
			LEFT JOIN `tabSituation Activity Link` sal ON sal.parent = sr.name
			WHERE sr.docstatus = 1
			  AND (%(from_date)s IS NULL OR DATE(sr.report_datetime) >= %(from_date)s)
			  AND (%(to_date)s IS NULL OR DATE(sr.report_datetime) <= %(to_date)s)
			GROUP BY sr.name
			ORDER BY sr.report_datetime DESC
		""",
		"filters": [
			{"fieldname": "from_date", "label": "From Date", "fieldtype": "Date"},
			{"fieldname": "to_date", "label": "To Date", "fieldtype": "Date"},
		],
		"columns": [],
	},
	{
		"report_name": "Threat Matrix",
		"module": "Operations",
		"ref_doctype": "Threat Assessment",
		"report_type": "Query Report",
		"query": """
			SELECT
				ta.assessment_date             AS `Assessment Date`,
				ta.sector                      AS `Sector`,
				ta.overall_threat_level        AS `Overall Threat`,
				COUNT(tal.name)                AS `Threat Lines`,
				ROUND(AVG(tal.threat_score), 1) AS `Avg Threat Score`,
				MAX(tal.capability)            AS `Max Capability`,
				MAX(tal.intent)                AS `Max Intent`,
				MAX(tal.opportunity)           AS `Max Opportunity`
			FROM `tabThreat Assessment` ta
			LEFT JOIN `tabThreat Assessment Line` tal ON tal.parent = ta.name
			WHERE ta.docstatus < 2
			GROUP BY ta.name
			ORDER BY ta.assessment_date DESC
		""",
		"filters": [],
		"columns": [],
	},
	{
		"report_name": "Casualty Summary",
		"module": "Operations",
		"ref_doctype": "Casualty Report",
		"report_type": "Query Report",
		"query": """
			SELECT
				cr.force_arrangement           AS `Observed Unit`,
				COUNT(*)                       AS `Reports`,
				SUM(cr.total_kia)              AS `Total KIA`,
				SUM(cr.total_wia)              AS `Total WIA`,
				SUM(cr.total_kia + cr.total_wia) AS `Total Casualties`,
				ROUND(AVG(cr.strength_pct_after), 1) AS `Avg Strength After`,
				MAX(cr.report_datetime)        AS `Last Report`
			FROM `tabCasualty Report` cr
			WHERE cr.docstatus = 1
			  AND (%(from_date)s IS NULL OR DATE(cr.report_datetime) >= %(from_date)s)
			  AND (%(to_date)s IS NULL OR DATE(cr.report_datetime) <= %(to_date)s)
			GROUP BY cr.force_arrangement
			ORDER BY `Total Casualties` DESC
		""",
		"filters": [
			{"fieldname": "from_date", "label": "From Date", "fieldtype": "Date"},
			{"fieldname": "to_date", "label": "To Date", "fieldtype": "Date"},
		],
		"columns": [],
	},
	# ------------------------------------------------------------------ Personnel
	{
		"report_name": "Personnel Roster",
		"module": "Personnel",
		"ref_doctype": "Personality",
		"report_type": "Query Report",
		"query": """
			SELECT
				p.personality_number           AS `Number`,
				p.personality_name             AS `Full Name`,
				p.rank_name                    AS `Rank`,
				p.evaluation_unit              AS `Evaluation Unit`,
				p.branch                       AS `Military Division`,
				p.rank_name                    AS `Rank`,  -- designation removed
				p.status                       AS `Status`,
				p.date_of_joining              AS `Joined`,
				p.cell_number                  AS `Mobile`,
				(SELECT COUNT(*) FROM `tabPersonality Dependent` d
				  WHERE d.parent = p.name)      AS `Dependents`
			FROM `tabPersonality` p
			WHERE (%(evaluation_unit)s IS NULL OR p.evaluation_unit = %(evaluation_unit)s)
			  AND (%(status)s IS NULL OR p.status = %(status)s)
			ORDER BY p.personality_name
		""",
		"filters": [
			{"fieldname": "evaluation_unit", "label": "Evaluation Unit",
			 "fieldtype": "Link", "options": "Evaluation Unit"},
			{"fieldname": "status", "label": "Status", "fieldtype": "Select",
			 "options": "\nActive\nInactive\nSuspended\nLeft"},
		],
		"columns": [],
	},
	{
		"report_name": "Rank Distribution",
		"module": "Personnel",
		"ref_doctype": "Personality",
		"report_type": "Query Report",
		"query": """
			SELECT
				IFNULL(p.rank_name, 'Unranked') AS `Rank`,
				COUNT(*)                        AS `Personnel`,
				SUM(CASE WHEN p.status = 'Active' THEN 1 ELSE 0 END) AS `Active`,
				SUM(CASE WHEN p.status = 'Left' THEN 1 ELSE 0 END)   AS `Left`,
				COUNT(DISTINCT p.evaluation_unit) AS `Units`
			FROM `tabPersonality` p
			GROUP BY p.rank_name
			ORDER BY `Personnel` DESC
		""",
		"filters": [],
		"columns": [],
	},
]


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------
def build_reports():
	"""Create / refresh every Query Report shipped with the app."""
	created, updated = 0, 0
	for spec in REPORT_SPECS:
		values = {
			"report_name": spec["report_name"],
			"ref_doctype": spec["ref_doctype"],
			"report_type": "Query Report",
			"module": spec["module"],
			"is_standard": "Yes",
			"query": spec["query"].strip(),
			"disabled": 0,
		}
		try:
			if frappe.db.exists("Report", spec["report_name"]):
				doc = frappe.get_doc("Report", spec["report_name"])
				doc.update(values)
				doc.flags.ignore_permissions = True
				doc.flags.ignore_links = True
				doc.save(ignore_permissions=True)
				updated += 1
			else:
				doc = frappe.get_doc({"doctype": "Report", **values})
				doc.flags.ignore_permissions = True
				doc.insert(ignore_permissions=True, set_name=spec["report_name"])
				created += 1
		except Exception as exc:  # noqa: BLE001
			frappe.log_error(
				title=f"Evaluation: report {spec['report_name']}", message=str(exc)
			)
			print(f"  ! {spec['report_name']}: {exc}")
	frappe.db.commit()
	print(_("Reports: {0} created, {1} updated").format(created, updated))


@frappe.whitelist()
def run_report(report_name: str, filters: dict | None = None):
	"""Execute a report by name and return ``columns`` + ``result`` rows.

	Used by the SPA / dashboards and handy from ``bench execute``.
	"""
	spec = next((s for s in REPORT_SPECS if s["report_name"] == report_name), None)
	if not spec:
		frappe.throw(_("Unknown report: {0}").format(report_name))

	values = {}
	for flt in spec["filters"]:
		raw = (filters or {}).get(flt["fieldname"])
		values[flt["fieldname"]] = raw or None

	rows = frappe.db.sql(spec["query"], values, as_dict=True)
	columns = list(rows[0].keys()) if rows else []
	return {"columns": columns, "result": rows}
