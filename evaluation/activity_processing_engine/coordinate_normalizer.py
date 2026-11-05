# Copyright (c) 2026, Aljahmi and contributors
# For license information, please see license.txt
"""توحيد الإحداثيات وتخزينها في Geolocation مع ربطها بالنشاط المصدر."""
from __future__ import annotations

import frappe
from frappe import _


def normalize_and_store(raw_text: str, latitude: float = None, longitude: float = None,
                        mgrs: str = None, source_activity: str = None,
                        coordinate_system: str = "degrees") -> str:
    """ينشئ أو يُعيد سجل Geolocation للإحداثيات المحددة."""
    # إذا يوجد نص خام فقط بدون إحداثيات، ننشئ سجلاً pendng للمراجعة
    if not latitude and not longitude and not mgrs:
        name = frappe.db.get_value(
            "Geolocation",
            {"raw_text": raw_text, "source_activity": source_activity},
            "name",
        )
        if name:
            return name
        doc = frappe.new_doc("Geolocation")
        doc.location_name = raw_text[:100] or "إحداثية غير محددة"
        doc.raw_text = raw_text
        doc.source_activity = source_activity
        doc.coordinate_system = coordinate_system
        doc.verification_status = "Unverified"
        doc.insert(ignore_permissions=True)
        return doc.name

    # البحث عن سجل موجود بنفس الإحداثيات
    existing = frappe.db.get_value(
        "Geolocation",
        {"latitude": latitude, "longitude": longitude},
        "name",
    )
    if existing:
        doc = frappe.get_doc("Geolocation", existing)
        if source_activity and source_activity not in (doc.source_activities or ""):
            doc.source_activities = (doc.source_activities or "") + "," + source_activity
        doc.save(ignore_permissions=True)
        return existing

    doc = frappe.new_doc("Geolocation")
    doc.location_name = raw_text[:100] or f"{latitude}, {longitude}"
    doc.raw_text = raw_text
    doc.latitude = latitude
    doc.longitude = longitude
    doc.mgrs = mgrs
    doc.coordinate_system = coordinate_system
    doc.source_activity = source_activity
    doc.verification_status = "Unverified"
    doc.insert(ignore_permissions=True)
    return doc.name
