# Copyright (c) 2026, Aljahmi and contributors
# For license information, please see license.txt
"""ربط الأنشطة بترتيب القوات (Force Arrangement) وتحديث المؤشرات بعد الاعتماد."""
from __future__ import annotations

import frappe
from frappe import _

from evaluation.activity_processing_engine.audit_trail import log_change


def suggest_unit_links(activity_name: str, observed_force: str = None,
                       governorate: str = None, context: str = "") -> list:
    """
    يقترح تشكيلات عسكرية محتملة من النشاط للعرض على المستخدم للمراجعة.
    يُعيد قائمة بالمرشحين مع درجات التشابه.
    """
    from evaluation.activity_processing_engine.entity_matcher import match_unit

    query = observed_force or ""
    if governorate:
        query = f"{governorate} {query}".strip()
    if not query:
        return []
    return match_unit(query, limit=5, threshold=0.45)


def link_activity_to_unit(activity_name: str, force_arrangement: str,
                          relationship: str = "observed",
                          notes: str = None, changed_by: str = None):
    """يربط نشاط يومي بتشكيل عسكري بعد اعتماد المستخدم."""
    try:
        activity = frappe.get_doc("Daily Activities", activity_name)
        activity.force_arrangement_link = force_arrangement
        activity.relationship_type = relationship
        if notes:
            activity.notes = (activity.notes or "") + "\n" + notes
        activity.save(ignore_permissions=True)

        # تحديث مؤشر التشكيل
        unit = frappe.get_doc("Force Arrangement", force_arrangement)
        unit.last_daily_activity = activity_name
        unit.last_observed = activity.date or frappe.utils.now_datetime()
        unit.save(ignore_permissions=True)

        log_change(
            entity_type="Force Arrangement",
            entity_name=force_arrangement,
            action="linked_activity",
            source_activity=activity_name,
            new_value=relationship,
            changed_by=changed_by or frappe.session.user,
            notes=notes or f"تم ربط النشاط {activity_name} بالتشكيل",
        )
        return True
    except Exception:
        frappe.db.rollback()
        return False
