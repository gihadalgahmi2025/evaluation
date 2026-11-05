# Copyright (c) 2026, Aljahmi and contributors
# For license information, please see license.txt
"""ربط الأشخاص المستخرجين من الأنشطة بملفات Personality مع سجل تدقيق كامل."""
from __future__ import annotations

import frappe
from frappe import _

from evaluation.activity_processing_engine.audit_trail import log_change


def create_or_link_personality(raw_name: str, normalized_name: str, source_activity: str,
                               context: str = "", role_hint: str = None,
                               confidence: float = 0.0) -> dict:
    """
    يُعيد قاموس:
      {
        "personality": name,      # اسم السجل في Personality
        "action": "linked"|"created_pending",
        "needs_review": bool,
        "candidates": list
      }
    """
    from evaluation.activity_processing_engine.entity_matcher import match_person

    candidates = match_person(normalized_name or raw_name, limit=5, threshold=0.50)

    # المطابقة الدقيقة
    if candidates and candidates[0]["score"] >= 0.90:
        personality = candidates[0]["name"]
        _link_activity_to_personality(personality, source_activity, context, confidence)
        log_change(
            entity_type="Personality",
            entity_name=personality,
            action="linked",
            source_activity=source_activity,
            new_value=raw_name,
            notes=f"مرتبط تلقائياً بالنشاط {source_activity} (تشابه {candidates[0]['score']})",
        )
        return {
            "personality": personality,
            "action": "linked",
            "needs_review": False,
            "candidates": candidates,
        }

    # لا توجد مطابقة دقيقة → إنشاء سجل مراجعة في انتظار اعتماد المستخدم
    doc = frappe.new_doc("Personality")
    doc.person_name = raw_name
    doc.normalized_name = normalized_name
    doc.status = "Under Review"
    doc.source_activity = source_activity
    doc.context = context
    doc.role_hint = role_hint
    doc.extraction_confidence = confidence
    doc.verification_status = "Unverified"
    doc.insert(ignore_permissions=True)

    log_change(
        entity_type="Personality",
        entity_name=doc.name,
        action="created_pending",
        source_activity=source_activity,
        new_value=raw_name,
        notes=f"سجل جديد تم إنشاؤه من النشاط {source_activity} بانتظار الاعتماد",
    )

    return {
        "personality": doc.name,
        "action": "created_pending",
        "needs_review": True,
        "candidates": candidates,
    }


def _link_activity_to_personality(personality: str, source_activity: str, context: str,
                                  confidence: float):
    """يربط النشاط بالسجل الشخصي في جدول فرعي إن وجد، وإلا ينشئ علاقة سجل."""
    try:
        activity = frappe.get_doc("Daily Activities", source_activity)
        # جدول فرعي Person Activity Link إن وجد في Doctype النشاط
        meta = frappe.get_meta("Daily Activities")
        if meta.has_field("person_links"):
            exists = any(
                row.personality == personality for row in (activity.person_links or [])
            )
            if not exists:
                activity.append("person_links", {
                    "personality": personality,
                    "context": context,
                    "confidence": confidence,
                    "source": "auto_extraction",
                })
                activity.save(ignore_permissions=True)
    except Exception:
        frappe.db.rollback()


def add_activity_link_on_personality(personality: str, activity_name: str,
                                     context: str = "", confidence: float = 0.0):
    """إضافة رابط نشاط في ملف الشخص (عند فتح ملف الشخص يُظهر الأنشطة المرتبطة)."""
    try:
        person = frappe.get_doc("Personality", personality)
        meta = frappe.get_meta("Personality")
        if meta.has_field("activity_links"):
            exists = any(
                row.activity == activity_name for row in (person.activity_links or [])
            )
            if not exists:
                person.append("activity_links", {
                    "activity": activity_name,
                    "context": context,
                    "confidence": confidence,
                    "linked_on": frappe.utils.now(),
                })
                person.save(ignore_permissions=True)
    except Exception:
        frappe.db.rollback()
