frappe.treeview_settings["Military Divisions"] = {
	breadcrumb: "Personnel",
	get_tree_root: false,
	fields: [
		{ fieldtype: "Data", fieldname: "military_divisions_name",
		  label: __("Military Divisions Name"), reqd: true },
	],
	extend_toolbar: false,
};
