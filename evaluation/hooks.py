# Copyright (c) 2026, Aljahmi and contributors
# For license information, please see license.txt
"""Evaluation - enemy reconnaissance app for Frappe Framework v16.

Modules
-------
Evaluation       Evaluation units, criteria, score cards, readiness & combat power
Reconnaissance   Daily observations, geography, spread layers
Order Of Battle  Enemy order of battle, force arrangement, logistics, fire support
Targeting        Targets, CARVER/BDA analysis, target categories
Operations       Operations orders, intel, situation reports, threat, casualties
Personnel        Persons under evaluation, ranks, affiliations, dependents
"""

app_name = "evaluation"
app_title = "Evaluation"
app_publisher = "Aljahmi"
app_description = "Enemy reconnaissance: order of battle, daily observations, targets, and situation"
app_email = "gihadalgahmi@gmail.com"
app_license = "MIT"
app_version = "0.1.0"

required_apps = ["frappe"]

# ---------------------------------------------------------------------------
# Includes - loaded on every desk page
# ---------------------------------------------------------------------------
app_include_css = "evaluation.bundle.css"
app_include_js = "evaluation.bundle.js"

doctype_js = {
	"Target": "public/js/target.js",
	"Daily Activities": "public/js/daily_activities.js",
	"Force Arrangement": "public/js/force_arrangement.js",
	"Personality": "public/js/personality.js",
}

doctype_list_js = {
	"Target": "public/js/list/target_list.js",
	"Daily Activities": "public/js/list/daily_activities_list.js",
}

# ---------------------------------------------------------------------------
# Document events
# ---------------------------------------------------------------------------
doc_events = {
	"*": {
		"validate": "evaluation.utils.validate_common_rules",
	},
	"Evaluation Criteria": {
		"validate": "evaluation.evaluation.doctype.evaluation_criteria.evaluation_criteria.validate_criteria",
	},
	"Evaluation Criteria Group": {
		"validate": "evaluation.evaluation.doctype.evaluation_criteria_group.evaluation_criteria_group.validate_group",
	},
	"Evaluation Score Card": {
		"validate": "evaluation.evaluation.doctype.evaluation_score_card.evaluation_score_card.compute_total",
		"on_update": "evaluation.evaluation.doctype.evaluation_score_card.evaluation_score_card.refresh_ranking",
	},
	"Force Arrangement": {
		"validate": "evaluation.order_of_battle.doctype.force_arrangement.force_arrangement.validate_force",
	},
	"Enemy Order of Battle": {
		"validate": "evaluation.order_of_battle.doctype.enemy_order_of_battle.enemy_order_of_battle.validate_ob",
	},
	"Daily Activities": {
		"validate": "evaluation.reconnaissance.doctype.daily_activities.daily_activities.validate_activity",
		"on_submit": "evaluation.reconnaissance.doctype.daily_activities.daily_activities.after_submit_activity",
		"on_cancel": "evaluation.reconnaissance.doctype.daily_activities.daily_activities.on_cancel_activity",
	},
	"Intel Report": {
		"validate": "evaluation.operations.doctype.intel_report.intel_report.validate_intel",
	},
	"Target": {
		"validate": "evaluation.targeting.doctype.target.target.validate_target",
		"on_update": "evaluation.targeting.doctype.target.target.log_status_change",
	},
	"Operation Order": {
		"validate": "evaluation.operations.doctype.operation_order.operation_order.validate_operation",
	},
	"Situation Report": {
		"validate": "evaluation.operations.doctype.situation_report.situation_report.validate_sitrep",
	},
	"Casualty Report": {
		"validate": "evaluation.operations.doctype.casualty_report.casualty_report.compute_casualties",
	},
	"Personality": {
		"before_save": "evaluation.personnel.doctype.personality.personality.set_full_name",
	},
	"Threat Assessment": {
		"validate": "evaluation.operations.doctype.threat_assessment.threat_assessment.compute_threat",
	},
}

# ---------------------------------------------------------------------------
# Scheduled tasks
# ---------------------------------------------------------------------------
scheduler_events = {
	"daily": [
		"evaluation.tasks.expire_targets",
		"evaluation.tasks.refresh_observation_freshness",
	],
	"weekly": [
		"evaluation.tasks.flag_stale_intel",
	],
	"hourly": ["evaluation.tasks.recompute_priority_scores"],
}

# ---------------------------------------------------------------------------
# Roles
# ---------------------------------------------------------------------------
ROLE_HIERARCHY = {
	"Evaluation Manager": ("Evaluation User",),
	"Evaluation Commander": ("Evaluation Manager",),
	"Evaluation Intel Officer": ("Evaluation User",),
	"Evaluation Ops Officer": ("Evaluation User",),
	"Evaluation Fires Officer": ("Evaluation User",),
	"Evaluation Logistics Officer": ("Evaluation User",),
}

permission_query_conditions = {
	"Daily Activities": "evaluation.permissions.daily_activities_query",
	"Intel Report": "evaluation.permissions.intel_report_query",
	"Target": "evaluation.permissions.target_query",
}

has_permission = {
	"Daily Activities": "evaluation.permissions.has_activity_permission",
	"Intel Report": "evaluation.permissions.has_intel_permission",
	"Target": "evaluation.permissions.has_target_permission",
}

# ---------------------------------------------------------------------------
# Global search
# ---------------------------------------------------------------------------
global_search_doctypes = {
	"Default": [
		{"doctype": "Target", "index": 1},
		{"doctype": "Enemy Order of Battle", "index": 2},
		{"doctype": "Force Arrangement", "index": 3},
		{"doctype": "Daily Activities", "index": 4},
		{"doctype": "Intel Report", "index": 5},
		{"doctype": "Situation Report", "index": 6},
		{"doctype": "Operation Order", "index": 7},
		{"doctype": "Personality", "index": 8},
		{"doctype": "Evaluation Unit", "index": 9},
		{"doctype": "Threat Assessment", "index": 10},
	]
}

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
fixtures = [
	{"dt": "Role", "filters": [["name", "like", "Evaluation%"]]},
	{"dt": "Workflow", "filters": [["document_type", "in", [
		"Daily Activities", "Intel Report", "Target", "Operation Order",
		"Situation Report", "Casualty Report", "Threat Assessment"]]]},
	{"dt": "Workflow State"},
	{"dt": "Workflow Action Master"},
	{"dt": "Notification", "filters": [["module", "=", "Evaluation"]]},
	{"dt": "Dashboard", "filters": [["module", "=", "Evaluation"]]},
	{"dt": "Dashboard Chart", "filters": [["module", "=", "Evaluation"]]},
	{"dt": "Number Card", "filters": [["module", "=", "Evaluation"]]},
	{"dt": "Report", "filters": [["module", "=", "Evaluation"], ["is_standard", "=", "Yes"]]},
	{"dt": "Print Format", "filters": [["module", "=", "Evaluation"]]},
]

# ---------------------------------------------------------------------------
# Boot, install, jinja
# ---------------------------------------------------------------------------
boot_session = "evaluation.boot.boot_session"

after_install = "evaluation.setup.after_install"
after_migrate = "evaluation.setup.after_migrate"
before_uninstall = "evaluation.setup.before_uninstall"

jinja = {
	"methods": [
		"evaluation.utils.get_force_display_name",
		"evaluation.utils.get_readiness_color",
		"evaluation.utils.get_unit_strength",
	],
	"filters": [
		"evaluation.utils.mask_coordinates",
		"evaluation.utils.format_mgrs",
	],
}

extend_doctype_class = {}
