<<<<<<< HEAD
// Copyright (c) 2026, Aljahmi and contributors
// For license information, please see license.txt
// Client script for Daily Activities — رابط محرك استخراج الكيانات والمراهنة المركزية

frappe.ui.form.on("Daily Activities", {
	refresh: function (frm) {
		// إظهار ملخص الاستخراج إذا كان قد تم معالجته
		if (frm.doc.entity_extraction_done) {
			frm.set_df_property("extraction_summary", "hidden", 0);
			if (frm.doc.extraction_summary) {
				frm.dashboard.set_message(
					`<span class="indicator indicator-info">تم استخراج الكيانات:</span> ${frm.doc.extraction_summary}`,
					true
				);
			}
		}

		// زر استخراج الكيانات يدوياً (للأدوار المسموحة)
		if (!frm.is_new() && frm.doc.docstatus === 1) {
			frm.add_custom_button(__("استخراج الكيانات ومراجعتها"), function () {
				frappe.call({
					method: "evaluation.activity_processing_engine.__init__.process_activity",
					args: { doc: frm.doc },
					freeze: true,
					freeze_message: __("يتم استخراج الكيانات من النشاط..."),
					callback: function (r) {
						if (r.message) {
							frm.refresh();
							frappe.msgprint({
								title: __("اكتمل الاستخراج"),
								message: r.message.summary || __("تم استخراج الكيانات بنجاح."),
								indicator: "green"
							});
						}
					}
				});
			}, __("المعالجة"));
		}

		// زر عرض السجلات المرتبطة بالشخص
		if (frm.doc.military_division) {
			frm.add_custom_button(__("عرض التشكيل المرتبط"), function () {
				frappe.set_route("Form", "Force Arrangement", frm.doc.military_division);
			}, __("التشكيلات"));
		}
	},

	before_save: function (frm) {
		// منع المستقبل
		if (frm.doc.start_of_event && frappe.datetime.get_date_diff(frm.doc.start_of_event, frappe.datetime.now_date()) > 0) {
			frappe.throw(__("لا يمكن تحديد تاريخ في المستقبل."));
		}
	},

	military_division: function (frm) {
		if (frm.doc.military_division) {
			frappe.call({
				method: "frappe.client.get_value",
				args: {
					doctype: "Force Arrangement",
					fieldname: ["current_posture", "governorate_name", "directorate_name", "evaluation_unit"],
					filters: { name: frm.doc.military_division }
				},
				callback: function (r) {
					if (r.message) {
						if (!frm.doc.governorate_name) frm.set_value("governorate_name", r.message.governorate_name);
						if (!frm.doc.directorate_name) frm.set_value("directorate_name", r.message.directorate_name);
						if (!frm.doc.evaluation_unit) frm.set_value("evaluation_unit", r.message.evaluation_unit);
					}
				}
			});
		}
	}
=======
// Daily Activities form
frappe.ui.form.on("Daily Activities", {
	onload(frm) {
		if (frm.is_new() && !frm.doc.start_of_event) {
			frm.set_value("start_of_event", frappe.datetime.get_today());
		}
	},
	refresh(frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(__("Create Intel Report"), () => {
				frm.call("create_intel_report").then((r) => {
					if (r.message) {
						frappe.show_alert({ message: __("Intel report {0}", [r.message]), indicator: "green" });
						frm.reload_doc();
					}
				});
			}, __("Create"));

			frm.add_custom_button(__("Nominate Target"), () => {
				frm.call("nominate_target").then((r) => {
					if (r.message) {
						frappe.set_route("Form", "Target", r.message);
					}
				});
			}, __("Create"));
		}

		if (frm.doc.inferred_posture) {
			frm.dashboard.add_indicator(__("Posture: {0}", [__(frm.doc.inferred_posture)]), "blue");
		}
		if (frm.doc.augmentation_and_reduction_div) {
			const color = frm.doc.augmentation_and_reduction_div === "Enhanced" ? "green" : "red";
			frm.dashboard.add_indicator(
				__("Strength {0}", [__(frm.doc.augmentation_and_reduction_div)]), color
			);
		}
	},
	military_division(frm) {
		if (!frm.doc.military_division) return;
		frappe.db.get_doc("Force Arrangement", frm.doc.military_division).then((unit) => {
			frm.set_value("inferred_posture", unit.current_posture);
			frm.set_value("governorate_name", unit.governorate_name);
			frm.set_value("directorate_name", unit.directorate_name);
			if (unit.evaluation_unit) frm.set_value("evaluation_unit", unit.evaluation_unit);
		});
	},
	generates_intel(frm) {
		if (frm.doc.generates_intel) {
			frm.set_df_property("generates_target", "description",
				__("An intel report will be created automatically on submit."));
		}
	},
>>>>>>> 85cd41117af485253bdbeafd604792de43fd6470
});
