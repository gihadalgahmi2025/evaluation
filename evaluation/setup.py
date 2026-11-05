# Copyright (c) 2026, Aljahmi and contributors
# For license information, please see license.txt
"""Install / migrate lifecycle for the Evaluation app.

``after_install`` builds the reference data the app needs to be usable on a
fresh site: roles, workflows, naming series, default criteria, readiness
metrics and the report/dashboard fixtures.  Everything is idempotent so it can
also be re-run from ``bench execute`` after a failed install.
"""

from __future__ import annotations

import frappe
from frappe import _

from evaluation.setup_data import BOOTSTRAP_DOCS, DEFAULT_ROLES, WORKFLOWS

# ---------------------------------------------------------------------------
# Lifecycle hooks
# ---------------------------------------------------------------------------
def after_install():
	frappe.flags.in_install_app = "evaluation"
	create_roles()
	create_custom_fields()
	create_workflows()
	seed_reference_data()
	create_workspaces()
	create_reports()
	create_dashboards()
	create_notifications()
	create_print_formats()
	create_email_templates()
	frappe.flags.in_install_app = None
	frappe.db.commit()
	print(_("Evaluation app initialised successfully."))


def after_migrate():
	create_roles()
	create_custom_fields()
	create_workflow_states()
	create_workflow_actions()
	sync_workflows()
	# refresh the derived desk surfaces so code changes reach existing sites
	create_workspaces()
	create_reports()
	create_dashboards()
	create_print_formats()


def before_uninstall():
	pass


# ---------------------------------------------------------------------------
# Roles
# ---------------------------------------------------------------------------
def create_roles():
	for role, description, desk_access in DEFAULT_ROLES:
		if frappe.db.exists("Role", role):
			continue
		doc = frappe.get_doc(
			{
				"doctype": "Role",
				"role_name": role,
				"desk_access": desk_access,
				"description": description,
			}
		)
		doc.insert(ignore_permissions=True)


# ---------------------------------------------------------------------------
# Custom fields on core doctypes
# ---------------------------------------------------------------------------
CUSTOM_FIELDS = [
	# User -> Evaluation Unit assignment (drives row level permissions)
	{
		"dt": "User",
		"fieldname": "evaluation_section",
		"fieldtype": "Section Break",
		"label": "Evaluation Access",
		"insert_after": "roles",
		"collapsible": 1,
	},
	{
		"dt": "User",
		"fieldname": "evaluation_role_profile",
		"fieldtype": "Link",
		"options": "Evaluation Designation",
		"label": "Evaluation Designation",
		"insert_after": "evaluation_section",
	},
	{
		"dt": "User",
		"fieldname": "evaluation_units",
		"fieldtype": "Small Text",
		"label": "Evaluation Units (comma separated)",
		"description": "Evaluation Units this user can access. Leave blank for all units allowed by role.",
		"insert_after": "evaluation_role_profile",
	},
	{
		"dt": "User",
		"fieldname": "evaluation_clearance",
		"fieldtype": "Select",
		"options": "\nUnclassified\nRestricted\nConfidential\nSecret",
		"label": "Intel Clearance Level",
		"default": "Unclassified",
		"insert_after": "evaluation_units",
	},
	# File -> attach intel documents to reports
	{
		"dt": "File",
		"fieldname": "evaluation_unit",
		"fieldtype": "Link",
		"options": "Evaluation Unit",
		"label": "Evaluation Unit",
		"insert_after": "folder",
		"read_only": 1,
	},
<<<<<<< HEAD
	# --- Activity Processing Engine custom fields ---
	{
		"dt": "Daily Activities",
		"fieldname": "entity_extraction_done",
		"fieldtype": "Check",
		"label": "تم استخراج الكيانات",
		"insert_after": "notes",
		"default": "0",
	},
	{
		"dt": "Daily Activities",
		"fieldname": "extraction_summary",
		"fieldtype": "Small Text",
		"label": "ملخص استخراج الكيانات",
		"insert_after": "entity_extraction_done",
		"read_only": 1,
	},
	{
		"dt": "Personality",
		"fieldname": "normalized_name",
		"fieldtype": "Data",
		"label": "الاسم الموحد",
		"insert_after": "person_name",
		"read_only": 1,
	},
	{
		"dt": "Personality",
		"fieldname": "extraction_confidence",
		"fieldtype": "Percent",
		"label": "درجة ثقة الاستخراج",
		"insert_after": "normalized_name",
		"default": "0",
	},
	{
		"dt": "Personality",
		"fieldname": "verification_status",
		"fieldtype": "Select",
		"label": "حالة التحقق",
		"options": "\nUnverified\nUnder Review\nVerified",
		"insert_after": "extraction_confidence",
		"default": "Unverified",
	},
=======
>>>>>>> 85cd41117af485253bdbeafd604792de43fd6470
]


def create_custom_fields():
	for spec in CUSTOM_FIELDS:
		name = f"{spec['dt']}-{spec['fieldname']}"
		if frappe.db.exists("Custom Field", name):
			continue
		doc = frappe.get_doc({"doctype": "Custom Field", **spec})
		doc.insert(ignore_permissions=True)


# ---------------------------------------------------------------------------
# Workflows
# ---------------------------------------------------------------------------
def create_workflows():
	create_workflow_states()
	create_workflow_actions()
	for spec in WORKFLOWS:
		sync_workflow(spec)


def create_workflow_states():
	states = {
		"Draft": "Inverse",
		"Pending Review": "Warning",
		"Validated": "Info",
		"Approved": "Success",
		"Active": "Primary",
		"Rejected": "Danger",
		"Closed": "Info",
		"Cancelled": "Danger",
	}
	for state, style in states.items():
		if frappe.db.exists("Workflow State", state):
			continue
		frappe.get_doc(
			{"doctype": "Workflow State", "workflow_state_name": state, "style": style}
		).insert(ignore_permissions=True)


def create_workflow_actions():
	for action in (
		"Submit for Review",
		"Validate",
		"Approve",
		"Reject",
		"Reopen",
		"Close",
		"Activate",
	):
		if frappe.db.exists("Workflow Action Master", action):
			continue
		frappe.get_doc(
			{"doctype": "Workflow Action Master", "workflow_action_name": action}
		).insert(ignore_permissions=True)


def sync_workflow(spec: dict):
	"""Create the workflow and its transitions, skipping anything already there."""
	name = spec.get("workflow_name")
	if frappe.db.exists("Workflow", name):
		return

	doc = frappe.get_doc(
		{
			"doctype": "Workflow",
			"workflow_name": name,
			"document_type": spec["document_type"],
			"workflow_state_field": "workflow_state",
			"is_active": 1,
			"send_email_alert": 0,
			"states": spec["states"],
			"transitions": spec["transitions"],
		}
	)
	doc.insert(ignore_permissions=True)


def sync_workflows():
	for spec in WORKFLOWS:
		sync_workflow(spec)


# ---------------------------------------------------------------------------
# Reference data (master records)
# ---------------------------------------------------------------------------
def seed_reference_data():
	if frappe.flags.in_test:
		return
	for doctype, rows in BOOTSTRAP_DOCS.items():
		for row in rows:
			insert_if_missing(doctype, row)


def insert_if_missing(doctype: str, values: dict, key_field: str | None = None):
	"""Insert ``values`` unless an identical key record already exists."""
	key_field = key_field or next(
		(f.fieldname for f in frappe.get_meta(doctype).fields if f.unique), "name"
	)
	if values.get(key_field) and frappe.db.exists(doctype, {key_field: values[key_field]}):
		return

	name = values.get(key_field) or values.get("name")
	if name and frappe.db.exists(doctype, name):
		return

	try:
		frappe.get_doc({"doctype": doctype, **values}).insert(ignore_permissions=True)
	except frappe.DuplicateEntryError:
		pass
	except frappe.ValidationError:
		pass


# ---------------------------------------------------------------------------
# Desk surfaces
# ---------------------------------------------------------------------------
def create_workspaces():
	from evaluation.workspace_builder import build_workspaces

	build_workspaces()


def create_reports():
	from evaluation.report_builder import build_reports

	build_reports()


def create_dashboards():
	from evaluation.dashboard_builder import build_dashboards, build_number_cards

	build_dashboards()
	build_number_cards()


def create_notifications():
	from evaluation.notification_builder import build_notifications

	build_notifications()


def create_print_formats():
	from evaluation.print_builder import build_print_formats

	build_print_formats()


def create_email_templates():
	from evaluation.notification_builder import build_email_templates

	build_email_templates()
