frappe.listview_settings["Daily Activities"] = {
	add_fields: ["docstatus", "workflow_state", "generates_intel", "generates_target"],
	get_indicator(doc) {
		if (doc.docstatus === 2) return [__("Cancelled"), "red", "docstatus,=,2"];
		if (doc.docstatus === 0) return [__("Draft"), "orange", "docstatus,=,0"];
		if (doc.generates_target) return [__("Target Raised"), "red", "generates_target,=,1"];
		if (doc.generates_intel) return [__("Intel Raised"), "blue", "generates_intel,=,1"];
		return [__("Submitted"), "green", "docstatus,=,1"];
	},
};
