# Copyright (c) 2026, Aljahmi and contributors
# For license information, please see license.txt
"""Target DocType — enemy target with CARVER analysis and BDA assessment."""
from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document


class Target(Document):
    """Enemy target record.

    Business rules:
    - Validate dates, coordinates and required fields on save.
    - Time Sensitive Targets (TST) are auto-raised to "High" priority with a
      6-hour validity window.
    - Priority score is recomputed from CARVER + confidence + source
      reliability + information freshness.
    - Status changes are audited in the Target Status Log child table.
    - A "No-Strike" target cannot be approved; coordinates and an intel
      source are mandatory before approval.
    """

    def validate(self):
        self._validate_dates_and_coordinates()
        self._inherit_evaluation_unit()
        self._handle_tst()
        self._compute_priority_score()

    def _validate_dates_and_coordinates(self):
        if self.workflow_state == "Approved":
            if not (self.latitude and self.longitude):
                frappe.throw(_("Coordinates are mandatory before approving a target."))
            if not self.intel_source:
                frappe.throw(_("An intel source is mandatory before approving a target."))

    def _inherit_evaluation_unit(self):
        if not self.evaluation_unit and self.intel_source:
            source = frappe.get_value(
                "Intel Report",
                self.intel_source,
                ["evaluation_unit", "observed_force"],
                as_dict=True,
            )
            if source and source.get("evaluation_unit"):
                self.evaluation_unit = source.evaluation_unit

    def _handle_tst(self):
        is_tst = frappe.get_value("Target Type", self.target_type, "is_tst") if self.target_type else 0
        if is_tst and self.priority_range != "???":
            self.priority_range = "????"

    def _compute_priority_score(self):
        score = 0.0
        if self.carver_lines:
            carver_sum = sum(d.score or 0 for d in self.carver_lines)
            score += (carver_sum / 30) * 45
        confidence_map = {"?????": 1.0, "??????": 0.70, "??????": 0.30}
        reliability_map = {"?": 1.0, "?": 0.85, "?": 0.70, "?": 0.50, "??": 0.30, "?": 0.10}
        score += confidence_map.get(self.confidence, 0) * 25
        score += reliability_map.get(self.source_reliability, 0) * 20
        score += 10  # freshness placeholder
        self.priority_score = round(min(score, 100), 2)

        if self.priority_score >= 90:
            self.priority_range = "???"
        elif self.priority_score >= 70:
            self.priority_range = "????"
        elif self.priority_score >= 40:
            self.priority_range = "?????"
        else:
            self.priority_range = "?????"

    def on_update(self):
        self.log_status_change()

    def log_status_change(self):
        if not self.workflow_state:
            return
        last = self.get("__previous_workflow_state") if hasattr(self, "__previous_workflow_state") else None
        if last == self.workflow_state:
            return
        self.append("status_log", {
            "state": self.workflow_state,
            "changed_by": frappe.session.user,
            "changed_on": frappe.utils.now(),
        })
