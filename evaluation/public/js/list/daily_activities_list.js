<<<<<<< HEAD
// Copyright (c) 2026, Aljahmi and contributors
// For license information, please see license.txt
// List view script for Daily Activities — فلاتر وعرض متقدم

frappe.listview_settings["Daily Activities"] = {
	add_fields: ["entity_extraction_done", "extraction_summary", "military_division", "start_of_event", "workflow_state"],
	get_indicator: function (doc) {
		if (doc.docstatus === 1) {
			if (doc.entity_extraction_done) {
				return [__("تم المعالجة"), "green", "entity_extraction_done,=,1"];
			}
			return [__("ينتظر المعالجة"), "orange", "entity_extraction_done,=,0"];
		}
		if (doc.docstatus === 2) {
			return [__("ملغي"), "red", "docstatus,=,2"];
		}
		return [__("مسودة"), "blue", "docstatus,=,0"];
	},
	format_indicator: function (doc) {
		if (doc.docstatus === 1) {
			if (doc.entity_extraction_done) {
				return [__("تم المعالجة"), "green"];
			}
			return [__("ينتظر المعالجة"), "orange"];
		}
		if (doc.docstatus === 2) {
			return [__("ملغي"), "red"];
		}
		return [__("مسودة"), "blue"];
	}
=======
frappe.listview_settings["Daily Activities"] = {
	add_fields: ["docstatus", "workflow_state", "generates_intel", "generates_target"],
	get_indicator(doc) {
		if (doc.docstatus === 2) return [__("Cancelled"), "red", "docstatus,=,2"];
		if (doc.docstatus === 0) return [__("Draft"), "orange", "docstatus,=,0"];
		if (doc.generates_target) return [__("Target Raised"), "red", "generates_target,=,1"];
		if (doc.generates_intel) return [__("Intel Raised"), "blue", "generates_intel,=,1"];
		return [__("Submitted"), "green", "docstatus,=,1"];
	},
>>>>>>> 85cd41117af485253bdbeafd604792de43fd6470
};
