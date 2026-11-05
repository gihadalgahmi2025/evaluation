# Copyright (c) 2026, Aljahmi and contributors
# For license information, please see license.txt
"""Smoke tests for Threat Assessment."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase


class TestThreatAssessment(FrappeTestCase):
	def test_doctype_metadata_loads(self):
		"""The DocType must have a valid meta and a resolvable controller."""
		meta = frappe.get_meta("Threat Assessment")
		self.assertEqual(meta.name, "Threat Assessment")
		self.assertTrue(meta.fields)

	def test_controller_imports(self):
		from frappe.model.document import get_controller

		controller = get_controller("Threat Assessment")
		self.assertTrue(controller)

	def test_required_fields_declared(self):
		"""Every mandatory field must carry a label so the UI is usable."""
		meta = frappe.get_meta("Threat Assessment")
		for field in meta.fields:
			if field.reqd and field.fieldtype not in ("Section Break", "Column Break", "Tab Break"):
				self.assertTrue(field.label, f"{field.fieldname} has no label")
