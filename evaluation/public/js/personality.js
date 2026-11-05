// Personality form
frappe.ui.form.on("Personality", {
	refresh(frm) {
		if (frm.is_new()) return;
		frm.add_custom_button(__("Organization Chart"), () => {
			frm.call("get_org_chart", { personality: frm.doc.name, depth: 3 }).then((r) => {
				frappe.msgprint({
					title: __("Reporting chain"),
					message: `<pre>${JSON.stringify(r.message, null, 2)}</pre>`,
					wide: true,
				});
			});
		}, __("View"));
	},
});
