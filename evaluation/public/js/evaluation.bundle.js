// Evaluation app - global desk assets
frappe.provide("evaluation");

evaluation.COLORS = {
	Critical: "red",
	High: "orange",
	Medium: "yellow",
	Low: "blue",
	Confirmed: "green",
	Probable: "orange",
	Doubtful: "gray",
};

evaluation.priority_indicator = function (priority) {
	return `<span class="indicator-pill ${evaluation.COLORS[priority] || "gray"}">${
		__(priority) || priority
	}</span>`;
};

// Colour the row indicator in list views based on priority / threat
$(document).on("app_loaded", () => {
	if (frappe.boot.evaluation) {
		frappe.utils.evaluation = frappe.boot.evaluation;
	}
});
