frappe.listview_settings["Target"] = {
	add_fields: ["priority", "status", "target_type", "priority_score", "no_strike"],
	get_indicator(doc) {
		if (doc.no_strike) return [__("No Strike"), "gray", "no_strike,=,1"];
		const colors = { Critical: "red", High: "orange", Medium: "yellow", Low: "blue" };
		return [__(doc.priority), colors[doc.priority] || "gray", `priority,=,${doc.priority}`];
	},
	onload(listview) {
		listview.page.add_action_item(__("Recompute Priorities"), () => {
			frappe.call({
				method: "evaluation.targeting.doctype.target.target.recompute_priorities",
				freeze: true,
				callback: () => listview.refresh(),
			});
		});
	},
};
