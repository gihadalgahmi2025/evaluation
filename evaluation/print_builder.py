# Copyright (c) 2026, Aljahmi and contributors
# For license information, please see license.txt
"""Print formats (WeasyPrint/HTML) shipped with the Evaluation app."""

from __future__ import annotations

import frappe
from frappe import _

BASE_STYLE = """
<style>
	.print-format { font-family: "Inter", "Segoe UI", sans-serif; font-size: 10pt; }
	.print-format h1 { font-size: 18pt; border-bottom: 2px solid #333; padding-bottom: 4px; }
	.print-format h2 { font-size: 12pt; margin-top: 14px; color: #333; }
	.print-format table { width: 100%; border-collapse: collapse; margin: 8px 0; }
	.print-format th, .print-format td { border: 1px solid #bbb; padding: 4px 6px; text-align: left; }
	.print-format th { background: #f2f2f2; }
	.print-format .label { color: #666; font-size: 8pt; text-transform: uppercase; }
	.print-format .value { font-weight: 600; }
	.print-format .grid { display: flex; flex-wrap: wrap; gap: 12px; }
	.print-format .cell { min-width: 28%; }
	.print-format .footer { margin-top: 18px; font-size: 8pt; color: #888; }
	.classification { text-align:center; font-weight:700; letter-spacing:2px;
					  border:2px solid #b71c1c; color:#b71c1c; padding:4px; margin-bottom:10px; }
</style>
"""

CLASSIFICATION = '<div class="classification">{{ frappe.db.get_value("Evaluation Unit", doc.evaluation_unit, "name") or "SECRET" }} - HANDLE VIA SECURE CHANNELS</div>'


PRINT_FORMATS = [
	{
		"name": "Target Dossier",
		"doc_type": "Target",
		"html": """
			{{ classification_bar }}
			<h1>{{ doc.target_name }}</h1>
			<div class="grid">
				<div class="cell"><div class="label">Target ID</div><div class="value">{{ doc.name }}</div></div>
				<div class="cell"><div class="label">Type</div><div class="value">{{ doc.target_type or "-" }}</div></div>
				<div class="cell"><div class="label">Priority</div><div class="value">{{ doc.priority }} ({{ doc.priority_score }})</div></div>
				<div class="cell"><div class="label">Confidence</div><div class="value">{{ doc.confidence or "-" }}</div></div>
				<div class="cell"><div class="label">Easting / Northing</div><div class="value">{{ doc.latitude or "-" }}, {{ doc.longitude or "-" }}</div></div>
				<div class="cell"><div class="label">MGRS</div><div class="value">{{ doc.mgrs or "-" }}</div></div>
				<div class="cell"><div class="label">Governorate</div><div class="value">{{ doc.governorate or "-" }}</div></div>
				<div class="cell"><div class="label">Directorate</div><div class="value">{{ doc.directorate or "-" }}</div></div>
			</div>

			<h2>CARVER Analysis</h2>
			<table>
				<tr><th>Criterion</th><th>Score</th><th>Notes</th></tr>
				{% for row in doc.carver_lines %}
				<tr><td>{{ row.criterion }}</td><td>{{ row.score }}</td><td>{{ row.notes or "" }}</td></tr>
				{% endfor %}
			</table>

			<h2>Battle Damage Assessment</h2>
			<table>
				<tr><th>Date</th><th>Damage Level</th><th>Assessed By</th><th>Restrike</th></tr>
				{% for row in doc.bda_lines %}
				<tr><td>{{ frappe.utils.format_datetime(row.assessment_datetime) }}</td>
					<td>{{ row.damage_level }}</td><td>{{ row.assessed_by or "" }}</td>
					<td>{{ _("Yes") if row.restrike_needed else _("No") }}</td></tr>
				{% endfor %}
			</table>

			<div class="footer">Generated {{ frappe.utils.now() }} by {{ frappe.session.user }}</div>
		""",
	},
	{
		"name": "Daily Observation Report",
		"doc_type": "Daily Activities",
		"html": """
			{{ classification_bar }}
			<h1>Daily Observation - {{ doc.name }}</h1>
			<div class="grid">
				<div class="cell"><div class="label">Observation Date</div><div class="value">{{ frappe.utils.format_date(doc.start_of_event) }}</div></div>
				<div class="cell"><div class="label">Collection Side</div><div class="value">{{ doc.activity_side }}</div></div>
				<div class="cell"><div class="label">Observer</div><div class="value">{{ doc.activity_worker or "-" }}</div></div>
				<div class="cell"><div class="label">Observed Unit</div><div class="value">{{ frappe.utils.get_force_display_name(doc.military_division) }}</div></div>
				<div class="cell"><div class="label">Governorate</div><div class="value">{{ doc.governorate_name or "-" }}</div></div>
				<div class="cell"><div class="label">Inferred Posture</div><div class="value">{{ doc.inferred_posture or "-" }}</div></div>
			</div>

			<h2>{{ doc.the_topic }}</h2>
			<p>{{ doc.text_summary or doc.notes or "" }}</p>

			{% if doc.readiness_changes %}
			<h2>Readiness Changes</h2>
			<table>
				<tr><th>Metric</th><th>Baseline</th><th>Adjustment</th><th>Resulting</th></tr>
				{% for row in doc.readiness_changes %}
				<tr><td>{{ row.readiness_metric }}</td><td>{{ row.baseline }}</td>
					<td>{{ row.adjustment }}</td><td>{{ row.resulting }}</td></tr>
				{% endfor %}
			</table>
			{% endif %}

			<div class="footer">Reported by {{ doc.creator_of_the_report }} on {{ frappe.utils.format_datetime(doc.date) }}</div>
		""",
	},
	{
		"name": "Situation Report",
		"doc_type": "Situation Report",
		"html": """
			{{ classification_bar }}
			<h1>SITREP {{ doc.name }}</h1>
			<div class="grid">
				<div class="cell"><div class="label">Reported</div><div class="value">{{ frappe.utils.format_datetime(doc.report_datetime) }}</div></div>
				<div class="cell"><div class="label">Sector</div><div class="value">{{ doc.sector }}</div></div>
				<div class="cell"><div class="label">Overall Status</div><div class="value">{{ doc.overall_status or "-" }}</div></div>
				<div class="cell"><div class="label">Weather</div><div class="value">{{ doc.weather or "-" }}</div></div>
			</div>
			<h2>Enemy Summary</h2>
			{{ doc.enemy_summary or "" }}
			<h2>Collection Notes</h2>
			{{ doc.friendly_summary or "" }}
			<h2>Unit Snapshot</h2>
			<table>
				<tr><th>Unit</th><th>Posture</th><th>Strength</th><th>Contact</th></tr>
				{% for row in doc.snapshot_lines %}
				<tr><td>{{ row.force_arrangement }}</td><td>{{ row.posture or "" }}</td>
					<td>{{ row.strength_pct or "" }}</td><td>{{ row.contact_status or "" }}</td></tr>
				{% endfor %}
			</table>
			<div class="footer">Generated {{ frappe.utils.now() }}</div>
		""",
	},
	{
		"name": "Intel Report",
		"doc_type": "Intel Report",
		"html": """
			{{ classification_bar }}
			<h1>INTREP {{ doc.name }}</h1>
			<div class="grid">
				<div class="cell"><div class="label">DTG</div><div class="value">{{ frappe.utils.format_datetime(doc.report_datetime) }}</div></div>
				<div class="cell"><div class="label">Source</div><div class="value">{{ doc.source_type }}</div></div>
				<div class="cell"><div class="label">Admiralty</div><div class="value">{{ doc.reliability }}{{ doc.credibility }}</div></div>
				<div class="cell"><div class="label">Eval Unit</div><div class="value">{{ doc.evaluation_unit }}</div></div>
			</div>
			<h2>{{ doc.subject }}</h2>
			{{ doc.details or "" }}
			<div class="footer">Generated {{ frappe.utils.now() }}</div>
		""",
	},
	{
		"name": "Force Arrangement Summary",
		"doc_type": "Force Arrangement",
		"html": """
			{{ classification_bar }}
			<h1>{{ doc.name_div }}</h1>
			<div class="grid">
				<div class="cell"><div class="label">Echelon</div><div class="value">{{ doc.size_div or "-" }}</div></div>
				<div class="cell"><div class="label">Posture</div><div class="value">{{ doc.current_posture or "-" }}</div></div>
				<div class="cell"><div class="label">Strength</div><div class="value">{{ doc.strength_pct }}%</div></div>
				<div class="cell"><div class="label">Combat Power Index</div><div class="value">{{ doc.combat_power_index }}</div></div>
				<div class="cell"><div class="label">Confidence</div><div class="value">{{ doc.observation_confidence or "-" }}</div></div>
				<div class="cell"><div class="label">Last Observation</div><div class="value">{{ frappe.utils.format_date(doc.date) }}</div></div>
			</div>
			<h2>Combat Effectiveness</h2>
			<table>
				<tr><th>Factor</th><th>Group</th><th>Value</th></tr>
				{% for row in doc.combat_effectiveness_lines %}
				<tr><td>{{ row.factor_name or row.combat_effectiveness_type }}</td>
					<td>{{ row.factor_group or "" }}</td><td>{{ row.value or "" }}</td></tr>
				{% endfor %}
			</table>
			<h2>Logistics</h2>
			<table>
				<tr><th>Class</th><th>On Hand</th><th>Days of Supply</th><th>Status</th></tr>
				{% for row in doc.logistics_lines %}
				<tr><td>{{ row.supply_class }}</td><td>{{ row.on_hand }}</td>
					<td>{{ row.days_of_supply }}</td><td>{{ row.status or "" }}</td></tr>
				{% endfor %}
			</table>
			<div class="footer">Generated {{ frappe.utils.now() }}</div>
		""",
	},
]


def build_print_formats():
	created = 0
	for spec in PRINT_FORMATS:
		if frappe.db.exists("Print Format", spec["name"]):
			continue
		try:
			html = BASE_STYLE + spec["html"].replace(
				"{{ classification_bar }}",
				'<div class="classification">HANDLE VIA SECURE CHANNELS</div>',
			)
			frappe.get_doc(
				{
					"doctype": "Print Format",
					"name": spec["name"],
					"doc_type": spec["doc_type"],
					"module": "Evaluation",
					"standard": "Yes",
					"print_format_type": "Jinja",
					"html": html,
					"custom_format": 0,
				}
			).insert(ignore_permissions=True, set_name=spec["name"])
			created += 1
		except Exception as exc:  # noqa: BLE001
			frappe.log_error(title=f"Evaluation print format {spec['name']}", message=str(exc))
	frappe.db.commit()
	return created
