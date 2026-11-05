# Copyright (c) 2026, Aljahmi and contributors
# For license information, please see license.txt
"""مطابقة الكيانات المستخرجة مع السجلات القائمة (فزي مبدئي)."""
from __future__ import annotations

import re
from typing import List, Optional, Tuple

import frappe
from frappe import _


def normalize_arabic_name(name: str) -> str:
    if not name:
        return ""
    name = name.strip()
    name = re.sub(r"\s+", " ", name)
    # إزالة التشكيل đơn
    name = re.sub(r"[\u064B-\u065F]", "", name)
    return name.lower()


def similarity_score(name_a: str, name_b: str) -> float:
    """نسبة تشابه بسيطة بين اسمين (0..1)."""
    a = normalize_arabic_name(name_a)
    b = normalize_arabic_name(name_b)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    # احتواء
    if a in b or b in a:
        return 0.85
    # تشابه حرفي بسيط (Jaccard على الكلمتين)
    set_a = set(a.split())
    set_b = set(b.split())
    if not set_a or not set_b:
        return 0.0
    inter = len(set_a & set_b)
    union = len(set_a | set_b)
    return inter / union if union else 0.0


class EntityMatcher:
    def __init__(self, doctype: str, name_field: str = "name"):
        self.doctype = doctype
        self.name_field = name_field

    def find_candidates(self, query: str, limit: int = 5, threshold: float = 0.45) -> List[dict]:
        if not query:
            return []
        # جلب السجلات التي تبدأ بالحرف الأول لتقليل النطاق
        first = query[0]
        rows = frappe.get_all(
            self.doctype,
            fields=[self.name_field, "name"],
            filters={self.name_field: ("like", f"{first}%")},
            limit=200,
        )
        scored = []
        for row in rows:
            label = row.get(self.name_field) or row.get("name")
            score = similarity_score(query, label)
            if score >= threshold:
                scored.append({
                    "doctype": self.doctype,
                    "name": row.get("name"),
                    "label": label,
                    "score": round(score, 2),
                })
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:limit]


def match_person(query: str, limit: int = 5) -> List[dict]:
    return EntityMatcher("Personality", "person_name").find_candidates(query, limit=limit)


def match_location(query: str, limit: int = 5) -> List[dict]:
    return EntityMatcher("Geolocation", "location_name").find_candidates(query, limit=limit)


def match_unit(query: str, limit: int = 5) -> List[dict]:
    return EntityMatcher("Force Arrangement", "name_div").find_candidates(query, limit=limit)
