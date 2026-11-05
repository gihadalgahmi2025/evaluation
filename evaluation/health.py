# Copyright (c) 2026, Aljahmi and contributors
# For license information, please see license.txt
"""Health checks for the Evaluation app.

Run with::

    bench --site mysite execute evaluation.health.run_checks

Returns a structured report so a deployment can verify that the environment,
the schema and the desk surfaces are all in place.
"""

from __future__ import annotations

import frappe
from frappe import _

MODULES = (
	"Evaluation",
	"Reconnaissance",
	"Order Of Battle",
	"Targeting",
	"Operations",
	"Personnel",
)


def _check(name: str, ok: bool, detail: str = "") -> dict:
	return {"check": name, "ok": bool(ok), "detail": detail}


def run_checks(verbose: bool = True) -> dict:
	"""Run every health check and return ``{"passed": n, "failed": n, "checks": [...]}``."""
	results: list[dict] = []

	# ------------------------------------------------------------------ runtime
	results.append(_check("frappe version >= 16", frappe.__version__.startswith("16."),
						  frappe.__version__))
	results.append(_check("python >= 3.14", _py_ok(), _py_version()))
	results.append(_check("site database reachable", _db_ok()))

	# ------------------------------------------------------------------ schema
	doctypes = frappe.get_all("DocType", filters={"module": ("in", MODULES)}, pluck="name")
	results.append(_check("evaluation doctypes installed", len(doctypes) >= 70,
						  f"{len(doctypes)} doctypes"))

	broken = _broken_controllers(doctypes)
	results.append(_check("all controllers importable", not broken,
						  ", ".join(broken) if broken else "ok"))

	missing_tables = [dt for dt in doctypes
					  if not frappe.get_meta(dt).istable and not frappe.db.table_exists(dt)]
	results.append(_check("all tables exist", not missing_tables,
						  ", ".join(missing_tables[:5]) if missing_tables else "ok"))

	# ------------------------------------------------------------- reference data
	for doctype, minimum in (
		("Evaluation Unit", 1),
		("Division Size", 5),
		("Division Type", 5),
		("Combat Posture", 5),
		("Readiness Metric", 5),
		("Supply Class", 5),
		("Target Type", 5),
		("Military Rank", 5),
	):
		count = frappe.db.count(doctype)
		results.append(_check(f"reference data: {doctype}", count >= minimum, f"{count} rows"))

	# ----------------------------------------------------------------- surfaces
	surfaces = (
		("Workspaces", frappe.db.count("Workspace", {"module": ("in", MODULES)}), 6),
		("Reports", frappe.db.count("Report", {"module": ("in", MODULES)}), 15),
		("Print Formats", frappe.db.count("Print Format", {"module": "Evaluation"}), 4),
		("Workflows", frappe.db.count("Workflow", {"document_type": ("in", [
			"Daily Activities", "Intel Report", "Target", "Operation Order",
			"Situation Report", "Threat Assessment"])}), 6),
		("Roles", frappe.db.count("Role", {"name": ("like", "Evaluation%")}), 7),
	)
	for label, count, minimum in surfaces:
		results.append(_check(f"desk surface: {label}", count >= minimum, f"{count}"))

	# ------------------------------------------------------------- broken reports
	bad_reports = _broken_reports()
	results.append(_check("all query reports execute", not bad_reports,
						  ", ".join(bad_reports[:5]) if bad_reports else "ok"))

	passed = sum(1 for r in results if r["ok"])
	failed = len(results) - passed

	if verbose:
		print(f"\nEvaluation health check — {passed} passed, {failed} failed\n")
		for row in results:
			mark = "✔" if row["ok"] else "✘"
			print(f"  {mark} {row['check']:44} {row['detail']}")

	return {"passed": passed, "failed": failed, "checks": results}


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _py_version() -> str:
	import platform

	return platform.python_version()


def _py_ok() -> bool:
	import sys

	return sys.version_info >= (3, 14)


def _db_ok() -> bool:
	try:
		frappe.db.sql("select 1")
		return True
	except Exception:
		return False


def _broken_controllers(doctypes: list[str]) -> list[str]:
	from frappe.model.document import import_controller

	broken = []
	for doctype in doctypes:
		try:
			import_controller(doctype)
		except Exception:
			broken.append(doctype)
	return broken


def _broken_reports() -> list[str]:
	from evaluation.report_builder import REPORT_SPECS, run_report

	broken = []
	for spec in REPORT_SPECS:
		try:
			run_report(spec["report_name"], {})
		except Exception:
			broken.append(spec["report_name"])
	return broken


@frappe.whitelist()
def health():
	"""Whitelisted variant for monitoring endpoints (``/api/method/evaluation.health.health``)."""
	report = run_checks(verbose=False)
	report["status"] = "ok" if report["failed"] == 0 else "degraded"
	return report
