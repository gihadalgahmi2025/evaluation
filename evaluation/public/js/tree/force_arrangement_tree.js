frappe.treeview_settings["Force Arrangement"] = {
	breadcrumb: "Order Of Battle",
	get_tree_root: false,
	filters: [{ fieldname: "evaluation_unit", label: __("Evaluation Unit"),
				fieldtype: "Link", options: "Evaluation Unit" }],
	fields: [
		{ fieldtype: "Data", fieldname: "name_div", label: __("Observed Unit Name"), reqd: true },
		{ fieldtype: "Link", fieldname: "size_div", label: __("Echelon"),
		  options: "Division Size" },
	],
	extend_toolbar: false,
};
