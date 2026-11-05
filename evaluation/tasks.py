# Copyright (c) 2026, Aljahmi and contributors
# For license information, please see license.txt
"""Scheduled background jobs for the Evaluation app.

Wired in ``hooks.py`` under ``scheduler_events``.  Every job is safe to run
twice and logs its own failures so one broken job never blocks the queue.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import add_days, cint, flt, now_datetime, nowdate

LOG_TITLE = "Evaluation scheduled job"


def _log(message: str):
	frappe.logger("evaluation").info(message)


# ---------------------------------------------------------------------------
# Daily
# ---------------------------------------------------------------------------
def expire_targets():
	"""Close targets whose validity window has passed."""
	from evaluation.targeting.doctype.target.target import expire_targets as _expire

	try:
		count = _expire()
		_log(f"expire_targets: {count} targets closed")
		return count
	except Exception:
		frappe.log_error(title=f"{LOG_TITLE}: expire_targets", message=frappe.get_traceback())
		return 0


def refresh_observation_freshness():
	"""Recompute readiness freshness and flag units with no recent observation."""
	threshold = add_days(nowdate(), -3)
	units = frappe.get_all(
		"Force Arrangement",
		filters={"is_group": 0},
		fields=["name", "last_observed", "observation_confidence"],
		limit_page_length=0,
	)
	stale = 0
	for unit in units:
		is_stale = not unit.last_observed or unit.last_observed < threshold
		if is_stale:
			stale += 1
			if unit.observation_confidence != "Doubtful":
				frappe.db.set_value(
					"Force Arrangement", unit.name,
					{"observation_confidence": "Doubtful"}, update_modified=False,
				)
	frappe.db.commit()
	_log(f"refresh_observation_freshness: {stale}/{len(units)} units stale")
	return stale


def rebuild_readiness_snapshots():
	"""Recalculate the combat power index of every observed unit."""
	from evaluation.order_of_battle.doctype.force_arrangement.force_arrangement import (
		recompute_all_indexes,
	)

	try:
		updated = recompute_all_indexes()
		_log(f"rebuild_readiness_snapshots: {updated} units updated")
		return updated
	except Exception:
		frappe.log_error(title=f"{LOG_TITLE}: rebuild_readiness_snapshots",
						 message=frappe.get_traceback())
		return 0


# ---------------------------------------------------------------------------
# Hourly
# ---------------------------------------------------------------------------
def recompute_priority_scores():
	"""Keep target priority scores in sync while intel ages."""
	from evaluation.targeting.doctype.target.target import recompute_priorities

	try:
		count = recompute_priorities()
		_log(f"recompute_priority_scores: {count} targets recalculated")
		return count
	except Exception:
		frappe.log_error(title=f"{LOG_TITLE}: recompute_priority_scores",
						 message=frappe.get_traceback())
		return 0


# ---------------------------------------------------------------------------
# Weekly
# ---------------------------------------------------------------------------
def flag_stale_intel():
	"""Mark intel reports older than 14 days that were never acted upon."""
	cutoff = add_days(nowdate(), -14)
	stale = frappe.get_all(
		"Intel Report",
		filters={
			"docstatus": 0,
			"report_datetime": ("<", cutoff),
			"linked_target": ("in", [None, ""]),
		},
		fields=["name", "subject", "evaluation_unit"],
		limit_page_length=200,
	)
	if not stale:
		return 0

	# one digest notification per evaluation unit instead of one per report
	by_unit: dict[str, list] = {}
	for row in stale:
		by_unit.setdefault(row.evaluation_unit or "Unassigned", []).append(row)

	for unit, rows in by_unit.items():
		recipients = _unit_recipients(unit)
		if not recipients:
			continue
		frappe.sendmail(
			recipients=recipients,
			subject=_("Evaluation: {0} stale intel report(s) in {1}").format(len(rows), unit),
			message=_build_stale_intel_message(rows),
			reference_doctype="Intel Report",
			reference_name=rows[0].name,
			now=True,
		)
	_log(f"flag_stale_intel: {len(stale)} reports flagged")
	return len(stale)


def purge_old_status_logs(days: int = 365):
	"""Delete target status log rows older than a year."""
	cutoff = add_days(nowdate(), -cint(days))
	deleted = frappe.db.sql(
		"""
		DELETE FROM `tabTarget Status Log`
		WHERE changed_on < %s
		""",
		(cutoff,),
	)
	frappe.db.commit()
	count = deleted or 0
	_log(f"purge_old_status_logs: {count} rows removed")
	return count


# ---------------------------------------------------------------------------
# Monthly
# ---------------------------------------------------------------------------
def archive_cancelled_docs(months: int = 12):
	"""Report (do not delete) old cancelled transactions for manual review."""
	cutoff = add_days(nowdate(), -30 * cint(months))
	summary = {}
	for doctype in ("Daily Activities", "Intel Report", "Target", "Situation Report"):
		summary[doctype] = frappe.db.count(
			doctype, {"docstatus": 2, "modified": ("<", cutoff)}
		)
	if any(summary.values()):
		frappe.log_error(
			title="Evaluation: cancelled documents ready for archive",
			message=frappe.as_json(summary),
		)
	return summary


# ---------------------------------------------------------------------------
# Cron (morning digest)
# ---------------------------------------------------------------------------
def morning_intel_digest():
	"""06:00 daily - one email per unit with the overnight picture."""
	units = frappe.get_all("Evaluation Unit", filters={"is_group": 0}, pluck="name")
	sent = 0
	for unit in units:
		recipients = _unit_recipients(unit)
		if not recipients:
			continue

		since = frappe.utils.add_to_date(now_datetime(), hours=-24)
		stats = {
			"observations": frappe.db.count(
				"Daily Activities", {"evaluation_unit": unit, "docstatus": 1,
									 "date": (">", since)}
			),
			"intel": frappe.db.count(
				"Intel Report", {"evaluation_unit": unit, "docstatus": 0,
								 "report_datetime": (">", since)}
			),
			"targets": frappe.db.count(
				"Target", {"evaluation_unit": unit, "status": "Active"}
			),
			"critical_threats": frappe.db.count(
				"Threat Assessment", {"evaluation_unit": unit,
									  "overall_threat_level": "Critical"}
			),
		}
		if not any(stats.values()):
			continue

		frappe.sendmail(
			recipients=recipients,
			subject=_("Evaluation morning digest - {0}").format(unit),
			message=_build_digest_message(unit, stats),
			now=True,
		)
		sent += 1
	_log(f"morning_intel_digest: {sent} digests sent")
	return sent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _unit_recipients(unit: str) -> list[str]:
	"""Users that should receive notifications for an evaluation unit."""
	users = frappe.get_all(
		"User",
		filters={
			"enabled": 1,
			"user_type": "System User",
			"evaluation_units": ("like", f"%{unit}%"),
		},
		pluck="email",
		limit_page_length=50,
	)
	return [u for u in users if u]


def _build_digest_message(unit: str, stats: dict) -> str:
	return f"""
	<h3>{_('Evaluation morning digest')} - {unit}</h3>
	<table class="table table-bordered" style="width:auto">
		<tr><td>{_('Observations (24h)')}</td><td><b>{stats['observations']}</b></td></tr>
		<tr><td>{_('New intel (24h)')}</td><td><b>{stats['intel']}</b></td></tr>
		<tr><td>{_('Active targets')}</td><td><b>{stats['targets']}</b></td></tr>
		<tr><td>{_('Critical threats')}</td><td><b>{stats['critical_threats']}</b></td></tr>
	</table>
	"""


def _build_stale_intel_message(rows: list) -> str:
	items = "".join(
		f"<li><a href='/app/intel-report/{r.name}'>{r.name}</a> - {r.subject}</li>"
		for r in rows[:50]
	)
	return f"<p>{_('These intel reports have not produced a target for 14 days:')}</p><ul>{items}</ul>"
