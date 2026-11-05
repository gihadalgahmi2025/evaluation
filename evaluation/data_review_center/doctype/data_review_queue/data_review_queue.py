# Copyright (c) 2026, Aljahmi and contributors
# For license information, please see license.txt
from __future__ import annotations
import frappe
from frappe import _
from frappe.model.document import Document


class DataReviewQueue(Document):
    def validate(self):
        if not self.created_on:
            self.created_on = frappe.utils.now()
