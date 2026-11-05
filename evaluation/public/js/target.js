<<<<<<< HEAD
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
=======
// Target form - live CARVER scoring and priority preview
frappe.ui.form.on("Target", {
	refresh(frm) {
		if (frm.doc.docstatus === 0) {
			frm.add_custom_button(__("Recalculate Priority"), () => {
				frm.call("compute_carver").then(() => frm.dirty());
			}, __("Actions"));
		}
		if (frm.doc.docstatus === 1) {
			frm.add_custom_button(__("Record BDA"), () => {
				const d = new frappe.ui.Dialog({
					title: __("Record Battle Damage Assessment"),
					fields: [
						{
							fieldname: "damage_level", fieldtype: "Select", label: __("Damage Level"),
							options: "No Damage\nLight\nModerate\nSevere\nDestroyed", reqd: 1,
						},
						{ fieldname: "notes", fieldtype: "Small Text", label: __("Notes") },
					],
					primary_action(values) {
						frm.call("record_bda", {
							damage_level: values.damage_level,
							notes: values.notes || "",
						}).then(() => {
							frm.reload_doc();
							d.hide();
						});
					},
				});
				d.show();
			}, __("Actions"));
		}
		if (frm.doc.no_strike) {
			frm.dashboard.set_headline_alert(
				__("This target is flagged NO STRIKE and cannot be approved."),
				"red"
			);
		}
		if (frm.doc.priority === "Critical") {
			frm.dashboard.set_headline_alert(
				__("Time critical target - coordinate with fires cell immediately."),
				"orange"
			);
		}
		render_carver(frm);
	},
	carver_lines_add(frm) { render_carver(frm); },
	carver_lines_remove(frm) { render_carver(frm); },
});

function render_carver(frm) {
	const rows = frm.doc.carver_lines || [];
	if (!rows.length) return;
	const total = rows.reduce((a, r) => a + (r.score || 0), 0);
	const max = rows.length * 5;
	const pct = max ? Math.round((total / max) * 100) : 0;
	frm.dashboard.add_indicator(
		__("CARVER {0}/{1} ({2}%)", [total, max, pct]),
		pct >= 75 ? "green" : pct >= 50 ? "orange" : "red"
	);
}
>>>>>>> 85cd41117af485253bdbeafd604792de43fd6470
