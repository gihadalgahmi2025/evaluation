# Copyright (c) 2026, Aljahmi and contributors
# For license information, please see license.txt
"""سجل التدقيق غير القابل للتلاعب لكل عملية تكامل بين الأنشطة والسجلات المركزية."""
from __future__ import annotations

import frappe
from frappe import _


def log_change(
    entity_type: str,
    entity_name: str,
    action: str,
    source_activity: str = None,
    source_doctype: str = None,
    source_name: str = None,
    old_value: str = None,
    new_value: str = None,
    changed_by: str = None,
    decision: str = None,
    notes: str = None,
):
    """تسجيل حدث تغيير في سجل التدقيق."""
    try:
        doc = frappe.get_doc({
            "doctype": "Data Change Log",
            "entity_type": entity_type,
            "entity_name": entity_name,
            "action": action,
            "source_activity": source_activity,
            "source_doctype": source_doctype,
            "source_name": source_name,
            "old_value": old_value,
            "new_value": new_value,
            "changed_by": changed_by or frappe.session.user,
            "decision": decision,
            "notes": notes,
            "timestamp": frappe.utils.now(),
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        return doc.name
    except Exception:
        # إذا لم يتم إنشاء DocType Data Change Log بعد، نتجاهل 침묵ياً أثناء التbootstrap
        frappe.db.rollback()
        return None
