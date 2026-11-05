# Copyright (c) 2026, Aljahmi and contributors
# For license information, please see license.txt
"""مركز المراجعة والاعتماد للبيانات المستخرجة من الأنشطة اليومية."""
from __future__ import annotations

import frappe
from frappe import _

from evaluation.activity_processing_engine.audit_trail import log_change


def enqueue_for_review(item_type: str, entity_name: str, source_activity: str,
                       proposed_value: str, confidence: float = 0.0,
                       reviewed_by: str = None) -> str:
    """إدراج عنصر في طابور المراجعة بانتظار اعتماد بشري."""
    doc = frappe.new_doc("Data Review Queue")
    doc.item_type = item_type
    doc.entity_name = entity_name
    doc.source_activity = source_activity
    doc.proposed_value = proposed_value
    doc.confidence = confidence
    doc.status = "Pending Review"
    doc.created_on = frappe.utils.now()
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    log_change(
        entity_type=item_type,
        entity_name=entity_name,
        action="queued_for_review",
        source_activity=source_activity,
        new_value=proposed_value,
        notes=f"تم إدراج {item_type} في قائمة المراجعة بانتظار الاعتماد",
    )
    return doc.name


def decide_review(review_queue_name: str, decision: str, decided_by: str = None,
                  final_value: str = None, target_entity: str = None,
                  merge_into: str = None, notes: str = None) -> dict:
    """
    اتخاذ قرار بشأن عنصر مراجعة:
    decision ∈ {Approved, Rejected, Merged, Archived}
    """
    queue = frappe.get_doc("Data Review Queue", review_queue_name)
    decided_by = decided_by or frappe.session.user

    decision_doc = frappe.new_doc("Data Review Decision")
    decision_doc.review_queue = review_queue_name
    decision_doc.item_type = queue.item_type
    decision_doc.entity_name = queue.entity_name
    decision_doc.source_activity = queue.source_activity
    decision_doc.proposed_value = queue.proposed_value
    decision_doc.decision = decision
    decision_doc.final_value = final_value or queue.proposed_value
    decision_doc.decided_by = decided_by
    decision_doc.decided_on = frappe.utils.now()
    decision_doc.notes = notes
    decision_doc.insert(ignore_permissions=True)

    queue.status = decision
    queue.decided_by = decided_by
    queue.decided_on = frappe.utils.now()
    queue.final_value = final_value or queue.proposed_value
    queue.save(ignore_permissions=True)

    # تنفيذ القرار على السجلات المركزية
    result = {"decision": decision, "entity": target_entity or queue.entity_name}

    if decision == "Approved" and queue.item_type == "Personality":
        result = _approve_personality(queue, final_value, decided_by)
    elif decision == "Merged" and queue.item_type == "Personality" and merge_into:
        result = _merge_personality(queue, merge_into, decided_by)
    elif decision == "Approved" and queue.item_type == "Location":
        result = _approve_location(queue, final_value, decided_by)
    elif decision == "Approved" and queue.item_type == "Force Unit":
        result = _approve_unit_link(queue, final_value, decided_by)

    frappe.db.commit()
    log_change(
        entity_type=queue.item_type,
        entity_name=queue.entity_name,
        action=f"review_{decision.lower()}",
        source_activity=queue.source_activity,
        old_value=queue.proposed_value,
        new_value=final_value,
        changed_by=decided_by,
        decision=decision,
        notes=notes,
    )
    result["review_decision"] = decision_doc.name
    return result


def _approve_personality(queue, final_value, decided_by):
    from evaluation.activity_processing_engine.personality_integrator import (
        add_activity_link_on_personality,
    )
    # إذا كان اسم الكيان جديداً، نستخدمه؛ وإلا نربط بالسجل الحالي
    personality = queue.entity_name
    add_activity_link_on_personality(
        personality, queue.source_activity, context="approved_from_review",
        confidence=queue.confidence,
    )
    return {"personality": personality, "action": "approved_and_linked"}


def _merge_personality(queue, merge_into, decided_by):
    # دمج السجل المكرر في السجل الرئيسي ونقل الروابط
    try:
        dup = frappe.get_doc("Personality", queue.entity_name)
        main = frappe.get_doc("Personality", merge_into)
        # نقل الروابط
        meta = frappe.get_meta("Personality")
        if meta.has_field("activity_links"):
            for row in dup.activity_links or []:
                add_activity_link_on_personality(
                    merge_into, row.activity, context=f"merged_from_{queue.entity_name}",
                    confidence=row.confidence,
                )
        dup.status = "Merged"
        dup.save(ignore_permissions=True)
        return {"personality": merge_into, "action": "merged"}
    except Exception:
        frappe.db.rollback()
        return {"error": "merge_failed"}


def _approve_location(queue, final_value, decided_by):
    from evaluation.activity_processing_engine.coordinate_normalizer import (
        normalize_and_store,
    )
    name = normalize_and_store(
        raw_text=queue.proposed_value,
        source_activity=queue.source_activity,
    )
    return {"location": name, "action": "approved_and_stored"}


def _approve_unit_link(queue, final_value, decided_by):
    from evaluation.activity_processing_engine.force_integrator import (
        link_activity_to_unit,
    )
    link_activity_to_unit(
        activity_name=queue.source_activity,
        force_arrangement=queue.entity_name,
        relationship="observed",
        notes=queue.notes,
        changed_by=decided_by,
    )
    return {"unit": queue.entity_name, "action": "linked"}
