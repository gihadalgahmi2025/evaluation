# Copyright (c) 2026, Aljahmi and contributors
# For license information, please see license.txt
"""Data Review Queue Report controller."""
from __future__ import annotations

import frappe


def execute(filters=None):
    """إرجاع أعمدة وبيانات تقرير قائمة المراجعة."""
    columns = [
        {"label": "معرف المراجعة", "fieldname": "review_id", "fieldtype": "Link", "options": "Data Review Queue", "width": 150},
        {"label": "النوع", "fieldname": "type", "fieldtype": "Data", "width": 100},
        {"label": "الكيان", "fieldname": "entity", "fieldtype": "Data", "width": 150},
        {"label": "النشاط المصدر", "fieldname": "activity", "fieldtype": "Link", "options": "Daily Activities", "width": 150},
        {"label": "القيمة المقترحة", "fieldname": "proposed", "fieldtype": "Small Text", "width": 200},
        {"label": "الثقة (%)", "fieldname": "confidence", "fieldtype": "Percent", "width": 80},
        {"label": "الحالة", "fieldname": "status", "fieldtype": "Data", "width": 100},
        {"label": "تاريخ الإنشاء", "fieldname": "created", "fieldtype": "Datetime", "width": 150},
        {"label": "تم اتخاذ القرار بواسطة", "fieldname": "decided_by", "fieldtype": "Link", "options": "User", "width": 120},
        {"label": "تاريخ القرار", "fieldname": "decided_on", "fieldtype": "Datetime", "width": 150},
        {"label": "ملاحظات", "fieldname": "notes", "fieldtype": "Small Text", "width": 200},
    ]

    conditions = "1=1"
    values = {}
    if filters:
        if filters.get("status"):
            conditions += " AND drq.status = %(status)s"
            values["status"] = filters["status"]
        if filters.get("item_type"):
            conditions += " AND drq.item_type = %(item_type)s"
            values["item_type"] = filters["item_type"]
        if filters.get("from_date"):
            conditions += " AND drq.created_on >= %(from_date)s"
            values["from_date"] = filters["from_date"]
        if filters.get("to_date"):
            conditions += " AND drq.created_on <= %(to_date)s"
            values["to_date"] = filters["to_date"]

    query = f"""
        SELECT
            drq.name AS review_id,
            drq.item_type AS type,
            drq.entity_name AS entity,
            drq.source_activity AS activity,
            drq.proposed_value AS proposed,
            drq.confidence AS confidence,
            drq.status AS status,
            drq.created_on AS created,
            drq.decided_by AS decided_by,
            drq.decided_on AS decided_on,
            drq.notes AS notes
        FROM `tabData Review Queue` drq
        WHERE {conditions}
        ORDER BY drq.created_on DESC
        LIMIT 500
    """

    data = frappe.db.sql(query, values, as_dict=True)
    return columns, data
