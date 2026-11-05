// Copyright (c) 2026, Aljahmi and contributors
// For license information, please see license.txt
// Client script for Force Arrangement — التشكيل مع الأنشطة المرتبطة

frappe.ui.form.on("Force Arrangement", {
	refresh: function (frm) {
		// زر عرض الأنشطة المرتبطة بالتشكيل
		if (!frm.is_new()) {
			frm.add_custom_button(__("الأنشطة المرصودة لهذا التشكيل"), function () {
				frappe.set_route("List", "Daily Activities", {
					military_division: frm.doc.name
				});
			}, __("الأنشطة"));
		}
	}
});
