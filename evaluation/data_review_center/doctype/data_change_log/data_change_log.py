# Copyright (c) 2026, Aljahmi and contributors
# For license information, please see license.txt
from __future__ import annotations
import frappe
from frappe import _
from frappe.model.document import Document


class DataChangeLog(Document):
    def validate(self):
        if not self.timestamp:
            self.timestamp = frappe.utils.now()
        if not self.changed_by:
            self.changed_by = frappe.session.user

    def on_trash(self):
        # منع الحذف لحماية سجل التدقيق
        frappe.throw(_("لا يمكن حذف سجلات التدقيق للمحافظة على سلامة السجل التاريخي."))
