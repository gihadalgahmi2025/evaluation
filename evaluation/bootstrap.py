# Copyright (c) 2026, Aljahmi and contributors
# For license information, please see license.txt
"""Bootstrap a *fresh* Evaluation site in one command.

Usage (from the bench directory)::

    bench --site mysite execute evaluation.bootstrap.bootstrap

or from a shell::

    cd ~/frappe-bench && env/bin/python -m evaluation.bootstrap

What it does
------------
1. creates the seven roles and the role hierarchy
2. creates the custom fields used for row level permissions
3. creates workflow states / actions / workflows for the transactional doctypes
4. seeds the reference tables (echelons, unit types, postures, supply classes,
   readiness metrics, target categories, fire support types ...)
5. builds the six workspaces, dashboards, charts, number cards
6. builds the seventeen query reports
7. builds the notifications, email templates and print formats

Every step is idempotent, so it is safe to run on an existing site.
"""

from __future__ import annotations

import frappe

STEPS = (
	("create_roles", "Roles"),
	("create_custom_fields", "Custom fields"),
	("create_workflow_states", "Workflow states"),
	("create_workflow_actions", "Workflow actions"),
	("sync_workflows", "Workflows"),
	("seed_reference_data", "Reference data"),
	("create_workspaces", "Workspaces"),
	("create_reports", "Reports"),
	("create_dashboards", "Dashboards"),
	("create_notifications", "Notifications"),
	("create_print_formats", "Print formats"),
	("create_email_templates", "Email templates"),
)


def bootstrap(verbose: bool = True):
	"""Run every initialisation step and return a summary dict."""
	from evaluation import setup

	summary = {"ok": [], "failed": []}

	for name, label in STEPS:
		fn = getattr(setup, name, None)
		if fn is None:
			summary["failed"].append((label, "missing function"))
			continue
		try:
			fn()
			frappe.db.commit()
			summary["ok"].append(label)
			if verbose:
				print(f"  ✔ {label}")
		except Exception as exc:  # noqa: BLE001
			frappe.db.rollback()
			summary["failed"].append((label, f"{type(exc).__name__}: {exc}"))
			if verbose:
				print(f"  ✘ {label}: {exc}")

	if verbose:
		print("\nBootstrap complete.")
		print(f"  succeeded: {len(summary['ok'])} steps")
		if summary["failed"]:
			print(f"  failed   : {len(summary['failed'])} steps")

	return summary


def install_demo_data(verbose: bool = True):
	"""Create a small but realistic dataset for demos and screenshots."""
	from evaluation.demo_data import create_demo_data

	result = create_demo_data()
	if verbose:
		print("Demo data:", result)
	return result


def reset_demo_data():
	"""Delete every document created by :func:`install_demo_data`."""
	from evaluation.demo_data import delete_demo_data

	return delete_demo_data()


if __name__ == "__main__":  # pragma: no cover
	bootstrap()
