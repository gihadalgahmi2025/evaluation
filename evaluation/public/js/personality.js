// Copyright (c) 2026, Aljahmi and contributors
// For license information, please see license.txt
// Client script for Personality — ملف الشخص مع الأنشطة المرتبطة

frappe.ui.form.on("Personality", {
	refresh: function (frm) {
		// إظهار حالة التحقق
		if (frm.doc.verification_status) {
			let status_color = {
				"Unverified": "orange",
				"Under Review": "blue",
				"Verified": "green"
			}[frm.doc.verification_status] || "grey";
			frm.dashboard.set_message(
				`<span class="indicator indicator-${status_color}">حالة التحقق: ${frm.doc.verification_status}</span>`,
				true
			);
		}

		// زر عرض الأنشطة المرتبطة
		if (!frm.is_new()) {
			frm.add_custom_button(__("الأنشطة المرتبطة بهذا الشخص"), function () {
				frappe.set_route("List", "Daily Activities", {
					"person_links.personality": frm.doc.name
				});
			}, __("الأنشطة"));
		}
	}
});
