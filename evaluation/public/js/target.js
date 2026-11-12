// Copyright (c) 2026, Aljahmi and contributors
// For license information, please see license.txt
// Client script for Target — الهدف مع تحليل CARVER وسجل الحالة

frappe.ui.form.on("Target", {
	refresh: function (frm) {
		// إغلاق الحقول المحسوبة تلقائياً
		frm.set_df_property("priority_score", "read_only", 1);
		frm.set_df_property("priority_range", "read_only", 1);

		// إذا كان الهدف حساس زمنياً، قفل نطاق الأولوية
		if (frm.doc.is_tst) {
			frm.set_df_property("priority_range", "read_only", 1);
		}

		// زر عرض التقرير الاستخباراتي المصدر
		if (frm.doc.intel_source) {
			frm.add_custom_button(__("عرض التقرير الاستخباراتي المصدر"), function () {
				frappe.set_route("Form", "Intel Report", frm.doc.intel_source);
			}, __("التقارير"));
		}
	},

	target_type: function (frm) {
		if (!frm.doc.target_type) return;
		frappe.call({
			method: "frappe.client.get_value",
			args: {
				doctype: "Target Type",
				fieldname: "is_tst",
				filters: { name: frm.doc.target_type }
			},
			callback: function (r) {
				if (r.message && r.message.is_tst) {
					frm.set_value("is_tst", 1);
				}
			}
		});
	}
});
