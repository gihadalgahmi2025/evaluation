frappe.treeview_settings["Personality"] = {
	breadcrumb: "Personnel",
	get_tree_root: false,
	fields: [
		{ fieldtype: "Data", fieldname: "personality_name", label: __("Full Name") },
	],
	extend_toolbar: false,
};
