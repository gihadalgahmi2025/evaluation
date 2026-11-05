# Copyright (c) 2026, Aljahmi and contributors
# For license information, please see license.txt
"""Activity Intelligence Report controller."""
from __future__ import annotations

import frappe


def execute(filters=None):
    """إرجاع أعمدة التقرير وبيانات الاستخبارات التشغيلية."""
    columns = [
        {"label": "النشاط", "fieldname": "activity", "fieldtype": "Link", "options": "Daily Activities", "width": 150},
        {"label": "التاريخ", "fieldname": "date", "fieldtype": "Date", "width": 100},
        {"label": "التشكيل", "fieldname": "unit", "fieldtype": "Link", "options": "Force Arrangement", "width": 150},
        {"label": "تم الاستخراج", "fieldname": "extracted", "fieldtype": "Check", "width": 80},
        {"label": "ملخص الكيانات", "fieldname": "summary", "fieldtype": "Small Text", "width": 300},
        {"label": "الحالة", "fieldname": "status", "fieldtype": "Data", "width": 100},
    ]

    conditions = "1=1"
    values = {}
    if filters:
        if filters.get("from_date"):
            conditions += " AND da.start_of_event >= %(from_date)s"
            values["from_date"] = filters["from_date"]
        if filters.get("to_date"):
            conditions += " AND da.start_of_event <= %(to_date)s"
            values["to_date"] = filters["to_date"]
        if filters.get("unit"):
            conditions += " AND da.military_division = %(unit)s"
            values["unit"] = filters["unit"]
        if filters.get("extracted") is not None:
            conditions += " AND da.entity_extraction_done = %(extracted)s"
            values["extracted"] = int(filters["extracted"])

    query = f"""
        SELECT
            da.name AS activity,
            da.start_of_event AS date,
            da.military_division AS unit,
            da.entity_extraction_done AS extracted,
            da.extraction_summary AS summary,
            da.workflow_state AS status
        FROM `tabDaily Activities` da
        WHERE {conditions}
        ORDER BY da.start_of_event DESC
        LIMIT 500
    """

    data = frappe.db.sql(query, values, as_dict=True)
    return columns, data
