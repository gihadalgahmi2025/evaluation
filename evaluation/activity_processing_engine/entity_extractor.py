# Copyright (c) 2026, Aljahmi and contributors
# For license information, please see license.txt
"""استخراج الكيانات (أشخاص، مواقع، جهات، تواريخ، أحداث) من نص النشاط اليومي."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

import frappe
from frappe import _


@dataclass
class ExtractedPerson:
    raw_name: str
    normalized_name: str
    role_hint: Optional[str] = None
    confidence: float = 0.0
    source_text: str = ""
    context: str = ""

    def to_dict(self) -> dict:
        return {
            "raw_name": self.raw_name,
            "normalized_name": self.normalized_name,
            "role_hint": self.role_hint,
            "confidence": self.confidence,
            "source_text": self.source_text,
            "context": self.context,
        }


@dataclass
class ExtractedLocation:
    raw_text: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    mgrs: Optional[str] = None
    coordinate_system: Optional[str] = None
    confidence: float = 0.0
    source_text: str = ""

    def to_dict(self) -> dict:
        return {
            "raw_text": self.raw_text,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "mgrs": self.mgrs,
            "coordinate_system": self.coordinate_system,
            "confidence": self.confidence,
            "source_text": self.source_text,
        }


@dataclass
class ExtractedEntity:
    entity_type: str  # person | location | organization | event | date
    value: str
    normalized_value: str
    confidence: float
    source_text: str
    start_index: int = 0
    end_index: int = 0
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "entity_type": self.entity_type,
            "value": self.value,
            "normalized_value": self.normalized_value,
            "confidence": self.confidence,
            "source_text": self.source_text,
            "start_index": self.start_index,
            "end_index": self.end_index,
            "metadata": self.metadata,
        }


class EntityExtractor:
    """محرك استخراج الكيانات من النصوص الحرة للنشاط اليومي."""

    # أنماط بسيطة لاستخراج الإحداثيات degrees و MGRS
    COORD_PATTERNS = [
        re.compile(r"(-?\d{1,3}(?:\.\d+)?)\s*[,°]\s*(-?\d{1,3}(?:\.\d+)?)"),
        re.compile(r"([0-9A-Z]{2}\s*\d{2}\s*\d{2}\s*\d{2})"),  # MGRS-light
    ]

    DATE_PATTERNS = [
        re.compile(r"\d{4}-\d{2}-\d{2}"),
        re.compile(r"\d{2}/\d{2}/\d{4}"),
        re.compile(r"\d{2}-\d{2}-\d{4}"),
    ]

    # كلمات دالة على الرتبة/المنصب العسكرية (بالعربية والإنجليزية)
    RANK_KEYWORDS = [
        "dec", "decoration", "ruluk", "r'ees", "raies", "قائد", "رائد", "عميد", "لواء", "فريق",
        "ضابط", "ملازم", "نقيب", "مقدم", "عقيد", "عميد", "فريق أول", "مشير", "Commander", "Colonel",
        "General", "Major", "Captain", "Lieutenant", "Sergeant", "Officer", "شخص", "individual",
    ]

    ORG_KEYWORDS = [
        "اللواء", "الفيلق", "الفريق", "الكتيبة", "السرب", "الوحدة", "الشعبة", "المديرية", "المحافظة",
        "brigade", "division", "corps", "battalion", "regiment", "company", "platoon", "squadron",
        "unit", "directorate", "governorate",
    ]

    def __init__(self, text: str, activity_name: str):
        self.text = text or ""
        self.activity_name = activity_name
        self.persons: List[ExtractedPerson] = []
        self.locations: List[ExtractedLocation] = []
        self.entities: List[ExtractedEntity] = []

    def extract(self) -> dict:
        self._extract_persons()
        self._extract_locations()
        self._extract_organizations()
        self._extract_dates()
        return {
            "persons": [p.to_dict() for p in self.persons],
            "locations": [l.to_dict() for l in self.locations],
            "entities": [e.to_dict() for e in self.entities],
        }

    def _add_entity(self, etype: str, value: str, normalized: str, confidence: float,
                    source: str, start: int = 0, end: int = 0, meta: dict = None):
        self.entities.append(ExtractedEntity(
            entity_type=etype,
            value=value,
            normalized_value=normalized,
            confidence=confidence,
            source_text=source,
            start_index=start,
            end_index=end,
            metadata=meta or {},
        ))

    def _extract_persons(self):
        """استخراج الأشخاص بناءً على كلمات دالة على الرتبة والصفات الوظيفية."""
        if not self.text:
            return
        # أنماط بسيطة: اسم بعد كلمة دالة
        pattern = re.compile(
            r"(?:" + "|".join(re.escape(k) for k in self.RANK_KEYWORDS) + r")\s+([^\d\n]{2,40})",
            re.IGNORECASE,
        )
        for m in pattern.finditer(self.text):
            raw = m.group(1).strip()
            norm = self._normalize_name(raw)
            self.persons.append(ExtractedPerson(
                raw_name=raw,
                normalized_name=norm,
                role_hint=m.group(0).split()[0] if m.group(0).split() else None,
                confidence=0.55,
                source_text=self.text[max(0, m.start() - 30): m.end() + 30],
                context="rank_keyword",
            ))
            self._add_entity(
                "person", raw, norm, 0.55,
                self.text[max(0, m.start() - 20): m.end() + 20],
                m.start(), m.end(), {"role_hint": m.group(0).split()[0] if m.group(0).split() else None}
            )

    def _extract_locations(self):
        """استخراج الإحداثيات النصية."""
        if not self.text:
            return
        for pat in self.COORD_PATTERNS:
            for m in pat.finditer(self.text):
                groups = m.groups()
                lat = lon = None
                sys = "degrees"
                if len(groups) >= 2:
                    try:
                        lat = float(groups[0])
                        lon = float(groups[1])
                    except ValueError:
                        pass
                self.locations.append(ExtractedLocation(
                    raw_text=m.group(0),
                    latitude=lat,
                    longitude=lon,
                    mgrs=groups[0] if len(groups) == 1 else None,
                    coordinate_system=sys,
                    confidence=0.70,
                    source_text=self.text[max(0, m.start() - 20): m.end() + 20],
                ))
                self._add_entity(
                    "location", m.group(0), m.group(0), 0.70,
                    self.text[max(0, m.start() - 20): m.end() + 20],
                    m.start(), m.end(), {"latitude": lat, "longitude": lon, "system": sys}
                )

    def _extract_organizations(self):
        if not self.text:
            return
        pattern = re.compile(
            r"(?:" + "|".join(re.escape(k) for k in self.ORG_KEYWORDS) + r")(?:\s+[^\d\n]{2,30})?",
            re.IGNORECASE,
        )
        for m in pattern.finditer(self.text):
            val = m.group(0).strip()
            norm = val.lower()
            self._add_entity(
                "organization", val, norm, 0.50,
                self.text[max(0, m.start() - 20): m.end() + 20],
                m.start(), m.end()
            )

    def _extract_dates(self):
        if not self.text:
            return
        for pat in self.DATE_PATTERNS:
            for m in pat.finditer(self.text):
                self._add_entity(
                    "date", m.group(0), m.group(0), 0.80,
                    self.text[max(0, m.start() - 10): m.end() + 10],
                    m.start(), m.end()
                )

    @staticmethod
    def _normalize_name(name: str) -> str:
        name = re.sub(r"\s+", " ", name.strip())
        return name


def extract_entities(text: str, activity_name: str) -> dict:
    """دالة مساعدة للاستدعاء من خارج الوحدة."""
    return EntityExtractor(text, activity_name).extract()
