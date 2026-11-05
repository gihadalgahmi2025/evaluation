# Copyright (c) 2026, Aljahmi and contributors
# For license information, please see license.txt
"""Unit tests for the Evaluation app core logic."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import nowdate, nowtime

from evaluation.utils import clamp, haversine_km, mask_coordinates, pct, weighted_average


class TestUtils(FrappeTestCase):
	def test_clamp(self):
		self.assertEqual(clamp(150), 100)
		self.assertEqual(clamp(-20), 0)
		self.assertEqual(clamp(55.5), 55.5)

	def test_pct(self):
		self.assertEqual(pct(25, 100), 25)
		self.assertEqual(pct(1, 0), 0)  # no ZeroDivisionError

	def test_weighted_average(self):
		self.assertEqual(weighted_average([(100, 1), (0, 1)]), 50)
		self.assertEqual(weighted_average([]), 0)
		self.assertEqual(weighted_average([(100, 0)]), 0)

	def test_haversine(self):
		# Sana'a -> Aden is roughly 300 km
		distance = haversine_km(15.3694, 44.1910, 12.7855, 45.0187)
		self.assertGreater(distance, 250)
		self.assertLess(distance, 350)

	def test_mask_coordinates(self):
		self.assertEqual(mask_coordinates("15.369412", 2), "15.37")

	def test_mgrs_format(self):
		from evaluation.utils import format_mgrs

		self.assertEqual(format_mgrs("38SMB45217834"), "38S MB 4521 7834")


class TestScoreCardEngine(FrappeTestCase):
	def setUp(self):
		self.criterion = frappe.get_doc(
			{
				"doctype": "Evaluation Criteria",
				"criterion_name": f"Test Criterion {frappe.generate_hash(length=6)}",
				"criterion_type": "Percentage",
				"applies_to": "Force Arrangement",
				"weight": 50,
				"max_value": 100,
				"is_active": 1,
			}
		).insert(ignore_permissions=True)

	def test_normalize_percentage(self):
		from evaluation.evaluation.doctype.evaluation_score_card.evaluation_score_card import (
			normalize_value,
		)

		self.assertAlmostEqual(normalize_value(self.criterion, 80), 0.8)
		self.assertAlmostEqual(normalize_value(self.criterion, 130), 1.0)

	def test_normalize_boolean(self):
		from evaluation.evaluation.doctype.evaluation_score_card.evaluation_score_card import (
			normalize_value,
		)

		self.criterion.criterion_type = "Boolean"
		self.assertEqual(normalize_value(self.criterion, 1), 1.0)
		self.assertEqual(normalize_value(self.criterion, 0), 0.0)

	def test_formula_is_sandboxed(self):
		from evaluation.evaluation.doctype.evaluation_score_card.evaluation_score_card import (
			safe_eval,
		)

		self.assertEqual(safe_eval("value * 2", {"value": 10}), 20)
		with self.assertRaises(Exception):
			safe_eval("__import__('os').system('echo hacked')", {})

	def tearDown(self):
		frappe.delete_doc("Evaluation Criteria", self.criterion.name, force=1,
						  ignore_permissions=True)


class TestTargetLogic(FrappeTestCase):
	def test_priority_score_bands(self):
		from evaluation.targeting.doctype.target.target import compute_priority_score
		from frappe.model.document import Document

		class FakeTarget(Document):
			def __init__(self, priority, carver):
				super().__init__({"doctype": "Target"})
				self.priority = priority
				self.confidence = "Probable"
				self.carver_lines = carver

		strong = [frappe._dict(criterion=c, score=5) for c in
				  ("Criticality", "Accessibility", "Recuperability",
				   "Vulnerability", "Effect", "Recognizability")]
		weak = [frappe._dict(criterion=c, score=1) for c in
				("Criticality", "Accessibility", "Recuperability",
				 "Vulnerability", "Effect", "Recognizability")]

		critical = compute_priority_score(FakeTarget("Critical", strong))
		low = compute_priority_score(FakeTarget("Low", weak))
		self.assertGreater(critical, low)
		self.assertGreaterEqual(critical, 90)
		self.assertLessEqual(low, 39)

	def test_threat_scale(self):
		from evaluation.operations.doctype.threat_assessment.threat_assessment import (
			compute_threat,
		)
		from frappe.model.document import Document

		doc = Document({"doctype": "Threat Assessment"})
		doc.assessment_date = nowdate()
		doc.threat_lines = [
			frappe._dict(capability=5, intent=5, opportunity=5, threat_score=0, idx=1),
			frappe._dict(capability=4, intent=4, opportunity=4, threat_score=0, idx=2),
		]
		compute_threat(doc)
		self.assertEqual(doc.overall_threat_level, "Critical")
		self.assertEqual(doc.threat_lines[0].threat_score, 100)


class TestPermissions(FrappeTestCase):
	def test_admin_has_no_scope(self):
		from evaluation.permissions import get_user_units

		frappe.set_user("Administrator")
		self.assertEqual(get_user_units(), [])

	def test_coordinate_masking(self):
		from evaluation.permissions import can_view_precise_coordinates

		frappe.set_user("Administrator")
		self.assertTrue(can_view_precise_coordinates())
