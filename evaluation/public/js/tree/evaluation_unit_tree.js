frappe.treeview_settings["Evaluation Unit"] = {
	breadcrumb: "Evaluation",
	get_tree_root: false,
	filters: [],
	fields: [
		{ fieldtype: "Data", fieldname: "unit_name", label: __("Unit Name"), reqd: true },
		{ fieldtype: "Data", fieldname: "abbreviation", label: __("Abbreviation") },
	],
	extend_toolbar: false,
};
