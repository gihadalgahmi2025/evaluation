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
});
