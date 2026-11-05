# Copyright (c) 2026, Aljahmi and contributors
# For license information, please see license.txt
"""Pending Reviews Dashboard controller."""
from __future__ import annotations

import frappe


def get_data(**kwargs):
    """إرجاع بيانات لوحة المراجعات المعلقة."""
    pending = frappe.db.count("Data Review Queue", {"status": "Pending Review"})
    approved = frappe.db.count("Data Review Queue", {"status": "Approved"})
    rejected = frappe.db.count("Data Review Queue", {"status": "Rejected"})
    merged = frappe.db.count("Data Review Queue", {"status": "Merged"})

    return {
        "total_pending": pending,
        "total_approved": approved,
        "total_rejected": rejected,
        "total_merged": merged,
        "labels": ["Pending Review", "Approved", "Rejected", "Merged"],
        "values": [pending, approved, rejected, merged],
    }
