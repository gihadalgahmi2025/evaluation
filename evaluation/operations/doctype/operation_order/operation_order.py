# Copyright (c) 2026, Aljahmi and contributors
# For license information, please see license.txt
"""Operation Order (OPORD) - enemy operation planning and execution."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, get_datetime, now_datetime

VALID_STATUS = ("Planned", "Approved", "Active", "Completed", "Cancelled", "Deferred")
VALID_TRANSITIONS = {
	"Planned": ("Approved", "Cancelled", "Deferred"),
	"Approved": ("Active", "Cancelled", "Deferred"),
	"Active": ("Completed", "Cancelled"),
	"Deferred": ("Planned", "Approved", "Cancelled"),
	"Completed": (),
	"Cancelled": ("Planned",),
}


class OperationOrder(Document):
	def validate(self):
		validate_operation(self, None)

	def before_save(self):
		previous = self.get_doc_before_save()
		if previous and previous.status != self.status:
			allowed = VALID_TRANSITIONS.get(previous.status, ())
			if self.status not in allowed:
				frappe.throw(
					_("Cannot move an operation from {0} to {1}").format(
						previous.status, self.status
					)
				)

	# ------------------------------------------------------------------ api
	@frappe.whitelist()
	def activate(self):
		self.status = "Active"
		self.save()
		return self.status

	@frappe.whitelist()
	def complete(self):
		self.status = "Completed"
		self.save()
		return self.status

	@frappe.whitelist()
	def progress(self) -> dict:
		total = len(self.tasks) or 1
		done = sum(1 for t in self.tasks if (t.status or "") == "Completed")
		return {"total": len(self.tasks), "completed": done, "pct": round(done * 100 / total, 1)}


def validate_operation(doc, method=None):
	if not doc.start_datetime:
		doc.start_datetime = now_datetime()

	if doc.end_datetime and get_datetime(doc.end_datetime) < get_datetime(doc.start_datetime):
		frappe.throw(_("End Datetime cannot be earlier than Start Datetime"))

	seen = set()
	for phase in doc.phases:
		if phase.phase_name in seen:
			frappe.throw(_("Duplicate phase: {0}").format(phase.phase_name))
		seen.add(phase.phase_name)

	for task in doc.tasks:
		if task.start_datetime and get_datetime(task.start_datetime) < get_datetime(doc.start_datetime):
			frappe.throw(
				_("Task {0} starts before the operation").format(
					task.task_code or f"#{task.idx}"
				)
			)
		if task.due_datetime and task.start_datetime:
			if get_datetime(task.due_datetime) < get_datetime(task.start_datetime):
				frappe.throw(
					_("Task {0} is due before it starts").format(task.task_code or f"#{task.idx}")
				)

	if doc.status == "Active" and not doc.assigned_forces:
		frappe.throw(_("An active operation must have assigned enemy units"))


@frappe.whitelist()
def sync_targets_with_operation(operation: str):
	"""Copy the operation's linked targets onto the target documents."""
	doc = frappe.get_doc("Operation Order", operation)
	updated = 0
	for row in doc.linked_targets:
		current = frappe.db.get_value("Target", row.target, "operation_order")
		if current != operation:
			frappe.db.set_value("Target", row.target, "operation_order", operation,
								update_modified=False)
			updated += 1
	frappe.db.commit()
	return updated
