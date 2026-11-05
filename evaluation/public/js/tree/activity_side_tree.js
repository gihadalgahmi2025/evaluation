frappe.treeview_settings["Activity Side"] = {
	breadcrumb: "Reconnaissance",
	get_tree_root: false,
	fields: [
		{ fieldtype: "Data", fieldname: "side_name", label: __("Activity Side Name"), reqd: true },
	],
	extend_toolbar: false,
};
