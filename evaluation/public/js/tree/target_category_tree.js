frappe.treeview_settings["Target Category"] = {
	breadcrumb: "Targeting",
	get_tree_root: false,
	fields: [
		{ fieldtype: "Data", fieldname: "category_name", label: __("Category Name"), reqd: true },
	],
	extend_toolbar: false,
};
