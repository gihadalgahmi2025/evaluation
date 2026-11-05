# Copyright (c) 2026, Aljahmi and contributors
# For license information, please see license.txt
"""Activity Processing Engine — استخراج الكيانات من الأنشطة اليومية وتغذية السجلات المركزية."""

from __future__ import annotations

import frappe
from frappe import _

from evaluation.activity_processing_engine.entity_extractor import extract_entities
from evaluation.activity_processing_engine.entity_matcher import match_person, match_unit, match_location
from evaluation.activity_processing_engine.review_center import enqueue_for_review
from evaluation.activity_processing_engine.coordinate_normalizer import normalize_and_store
from evaluation.activity_processing_engine.personality_integrator import (
    create_or_link_personality,
    add_activity_link_on_personality,
)
from evaluation.activity_processing_engine.force_integrator import suggest_unit_links, link_activity_to_unit
from evaluation.activity_processing_engine.audit_trail import log_change


def process_activity(doc) -> dict:
    """
    نقطة الدخول الرئيسية لمعالجة نشاط يومي بعد الإرسال.
    تستخرج الكيانات، تنشرها لمركز المراجعة، وتربط بالسجلات بعد الاعتماد.
    """
    activity_name = doc.name
    text = doc.text_summary or doc.notes or doc.the_topic or ""

    # 1. استخراج الكيانات من نص النشاط
    extracted = extract_entities(text, activity_name)

    summary_parts = []

    # 2. معالجة الأشخاص المستخرجين
    for p in extracted.get("persons", []):
        result = create_or_link_personality(
            raw_name=p["raw_name"],
            normalized_name=p["normalized_name"],
            source_activity=activity_name,
            context=p.get("context", ""),
            role_hint=p.get("role_hint"),
            confidence=p.get("confidence", 0.0),
        )
        if result["needs_review"]:
            enqueue_for_review(
                item_type="Personality",
                entity_name=result["personality"],
                source_activity=activity_name,
                proposed_value=p["raw_name"],
                confidence=p.get("confidence", 0.0),
            )
            summary_parts.append(f"شخص pending: {p['raw_name']}")
        else:
            add_activity_link_on_personality(
                result["personality"], activity_name,
                context=p.get("context", ""), confidence=p.get("confidence", 0.0),
            )
            summary_parts.append(f"شخص مرتبط: {p['raw_name']}")

    # 3. معالجة المواقع والإحداثيات
    for loc in extracted.get("locations", []):
        if loc.get("latitude") or loc.get("longitude") or loc.get("mgrs"):
            loc_name = normalize_and_store(
                raw_text=loc["raw_text"],
                latitude=loc.get("latitude"),
                longitude=loc.get("longitude"),
                mgrs=loc.get("mgrs"),
                source_activity=activity_name,
                coordinate_system=loc.get("coordinate_system", "degrees"),
            )
            enqueue_for_review(
                item_type="Location",
                entity_name=loc_name,
                source_activity=activity_name,
                proposed_value=loc["raw_text"],
                confidence=loc.get("confidence", 0.0),
            )
            summary_parts.append(f"موقع: {loc['raw_text']}")
        else:
            enqueue_for_review(
                item_type="Location",
                entity_name=loc["raw_text"][:100],
                source_activity=activity_name,
                proposed_value=loc["raw_text"],
                confidence=loc.get("confidence", 0.0),
            )
            summary_parts.append(f"موقع غير محدد: {loc['raw_text']}")

    # 4. اقتراح ربط بتشكيل عسكري
    if doc.military_division:
        candidates = suggest_unit_links(
            activity_name, observed_force=doc.military_division,
            governorate=doc.governorate_name, context="observed_unit",
        )
        if candidates:
            # ربط تلقائي بأفضل مرشح إذا كان التشكيل موجوداً فعلاً
            best = candidates[0]
            if best["score"] >= 0.80:
                link_activity_to_unit(
                    activity_name, best["name"],
                    relationship="observed",
                    notes=f"مرشح تلقائي (تشابه {best['score']})",
                )
                summary_parts.append(f"ترابط تشكيل: {best['label']}")
            else:
                enqueue_for_review(
                    item_type="Force Unit",
                    entity_name=doc.military_division,
                    source_activity=activity_name,
                    proposed_value=doc.military_division,
                    confidence=best["score"],
                )
                summary_parts.append(f"تشكيل pending: {doc.military_division}")

    # 5. تحديث حالة النشاط
    frappe.db.set_value(
        "Daily Activities", activity_name,
        {
            "entity_extraction_done": 1,
            "extraction_summary": "; ".join(summary_parts) if summary_parts else "لا توجد كيانات مستخرجة",
        },
        update_modified=False,
    )
    frappe.db.commit()

    log_change(
        entity_type="Daily Activities",
        entity_name=activity_name,
        action="processed",
        source_activity=activity_name,
        new_value="; ".join(summary_parts),
        notes="تم معالجة النشاط بواسطة Activity Processing Engine",
    )

    return {
        "activity": activity_name,
        "extracted": extracted,
        "summary": "; ".join(summary_parts),
    }
