# Copyright (c) 2026, Aljahmi and contributors
# For license information, please see license.txt
from __future__ import annotations
import frappe
from frappe import _
from frappe.model.document import Document


class DataReviewDecision(Document):
    def validate(self):
        if not self.decided_on:
            self.decided_on = frappe.utils.now()
        if not self.decided_by:
            self.decided_by = frappe.session.user
