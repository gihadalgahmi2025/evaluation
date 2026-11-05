# Copyright (c) 2026, Aljahmi and contributors
# For license information, please see license.txt
"""Notifications and email templates shipped with the Evaluation app."""

from __future__ import annotations

import frappe
from frappe import _

#: (name, document_type, event, subject, condition, message, recipients)
NOTIFICATIONS = [
	{
		"name": "New Critical Target",
		"document_type": "Target",
		"event": "Value Change",
		"value_changed": "priority",
		"condition": 'doc.priority == "Critical" and doc.docstatus < 2',
		"subject": _("Critical target nominated: {{ doc.target_name }}"),
		"message": """
			<p>A target was raised to <b>Critical</b> priority.</p>
			<ul>
				<li>Target: <a href="/app/target/{{ doc.name }}">{{ doc.target_name }}</a></li>
				<li>Type: {{ doc.target_type or "-" }}</li>
				<li>Unit: {{ doc.evaluation_unit }}</li>
				<li>Confidence: {{ doc.confidence or "-" }}</li>
			</ul>
		""",
		"roles": ["Evaluation Commander", "Evaluation Intel Officer", "Evaluation Fires Officer"],
	},
	{
		"name": "Intel Report Submitted",
		"document_type": "Intel Report",
		"event": "Submit",
		"subject": _("Intel report {{ doc.name }} submitted"),
		"message": """
			<p>{{ doc.subject }}</p>
			<p>Source: {{ doc.source_type }} ({{ doc.reliability }}{{ doc.credibility }})</p>
			<p><a href="/app/intel-report/{{ doc.name }}">Open report</a></p>
		""",
		"roles": ["Evaluation Intel Officer", "Evaluation Manager"],
	},
	{
		"name": "Observation Stale",
		"document_type": "Force Arrangement",
		"event": "Value Change",
		"value_changed": "last_observed",
		"condition": "0",  # raised by the scheduled job instead
		"subject": _("No observation for {{ doc.name_div }}"),
		"message": "<p>Unit {{ doc.name_div }} has not been observed recently.</p>",
		"roles": ["Evaluation Intel Officer"],
		"disabled": 1,
	},
	{
		"name": "Score Card Approved",
		"document_type": "Evaluation Score Card",
		"event": "Value Change",
		"value_changed": "status",
		"condition": 'doc.status == "Approved"',
		"subject": _("Score card {{ doc.name }} approved"),
		"message": """
			<p>{{ doc.score_card_title }} - total score <b>{{ doc.total_score }}</b></p>
			<p>Rank: {{ doc.rank }}</p>
		""",
		"roles": ["Evaluation Manager"],
	},
]


def build_notifications():
	created = 0
	for spec in NOTIFICATIONS:
		name = spec["name"]
		if frappe.db.exists("Notification", name):
			continue
		try:
			doc = frappe.get_doc(
				{
					"doctype": "Notification",
					"name": name,
					"subject": spec["subject"],
					"document_type": spec["document_type"],
					"event": spec["event"],
					"value_changed": spec.get("value_changed"),
					"condition": spec.get("condition") or "",
					"message": spec["message"],
					"channel": "System Notification",
					"enabled": 0 if spec.get("disabled") else 1,
					"module": "Evaluation",
					"is_standard": 1,
					"send_system_notification": 1,
					"send_email": 1,
					"recipients": [{"receiver_by_role": r} for r in spec["roles"]],
				}
			)
			doc.flags.ignore_permissions = True
			doc.insert(ignore_permissions=True, set_name=name)
			created += 1
		except Exception as exc:  # noqa: BLE001
			frappe.log_error(title=f"Evaluation notification {name}", message=str(exc))
	frappe.db.commit()
	return created


EMAIL_TEMPLATES = [
	{
		"name": "Evaluation Morning Digest",
		"subject": _("Evaluation morning digest - {{ unit }}"),
		"response": """
			<p>Good morning,</p>
			<p>Here is the overnight reconnaissance picture for <b>{{ unit }}</b>:</p>
			{{ stats_table }}
			<p><a href="/app/evaluation">Open Evaluation</a></p>
		""",
	},
	{
		"name": "Evaluation Critical Target Alert",
		"subject": _("Critical target: {{ target_name }}"),
		"response": """
			<p>A <b>critical</b> priority target has been nominated.</p>
			<ul>
				<li>Target: {{ target_name }}</li>
				<li>Unit: {{ unit }}</li>
				<li>Priority score: {{ score }}</li>
			</ul>
		""",
	},
]


def build_email_templates():
	created = 0
	for spec in EMAIL_TEMPLATES:
		if frappe.db.exists("Email Template", spec["name"]):
			continue
		try:
			frappe.get_doc(
				{
					"doctype": "Email Template",
					"name": spec["name"],
					"subject": spec["subject"],
					"response": spec["response"],
					"use_html": 1,
				}
			).insert(ignore_permissions=True, set_name=spec["name"])
			created += 1
		except Exception as exc:  # noqa: BLE001
			frappe.log_error(title=f"Evaluation email template {spec['name']}", message=str(exc))
	frappe.db.commit()
	return created
