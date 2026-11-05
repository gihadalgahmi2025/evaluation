frappe.treeview_settings["Enemy Order of Battle"] = {
	breadcrumb: "Order Of Battle",
	get_tree_root: false,
	filters: [{ fieldname: "evaluation_unit", label: __("Evaluation Unit"),
				fieldtype: "Link", options: "Evaluation Unit" }],
	fields: [
		{ fieldtype: "Data", fieldname: "unit_name", label: __("Unit Name"), reqd: true },
		{ fieldtype: "Data", fieldname: "unit_type", label: __("Unit Type") },
		{ fieldtype: "Int", fieldname: "estimated_strength", label: __("Estimated Strength") },
	],
	extend_toolbar: false,
};
