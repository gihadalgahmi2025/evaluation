# Copyright (c) 2026, Aljahmi and contributors
# For license information, please see license.txt
"""Smoke tests for Supply Class."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase


class TestSupplyClass(FrappeTestCase):
	def test_doctype_metadata_loads(self):
		"""The DocType must have a valid meta and a resolvable controller."""
		meta = frappe.get_meta("Supply Class")
		self.assertEqual(meta.name, "Supply Class")
		self.assertTrue(meta.fields)

	def test_controller_imports(self):
		from frappe.model.document import get_controller

		controller = get_controller("Supply Class")
		self.assertTrue(controller)

	def test_required_fields_declared(self):
		"""Every mandatory field must carry a label so the UI is usable."""
		meta = frappe.get_meta("Supply Class")
		for field in meta.fields:
			if field.reqd and field.fieldtype not in ("Section Break", "Column Break", "Tab Break"):
				self.assertTrue(field.label, f"{field.fieldname} has no label")
