// Force Arrangement form - combat power visualisation
frappe.ui.form.on("Force Arrangement", {
	refresh(frm) {
		if (frm.is_new()) return;

		frm.add_custom_button(__("Refresh Combat Power"), () => {
			frm.call("refresh_index").then(() => frm.reload_doc());
		}, __("Actions"));

		frm.add_custom_button(__("View Sub-units"), () => {
			frm.call("get_subtree").then((r) => show_subtree(r.message, frm.doc.name_div));
		}, __("Actions"));

		if (frm.doc.combat_power_index) {
			const cpi = frm.doc.combat_power_index;
			frm.dashboard.add_indicator(
				__("Combat Power {0}", [cpi]),
				cpi >= 75 ? "green" : cpi >= 50 ? "orange" : "red"
			);
		}
		if (frm.doc.strength_pct !== undefined) {
			frm.dashboard.add_indicator(
				__("Strength {0}%", [frm.doc.strength_pct]),
				frm.doc.strength_pct >= 80 ? "green" :
				frm.doc.strength_pct >= 60 ? "orange" : "red"
			);
		}
	},
});

function show_subtree(rows, title) {
	const html = `
		<table class="table table-bordered">
			<thead><tr>
				<th>${__("Unit")}</th><th>${__("Echelon")}</th>
				<th>${__("Posture")}</th><th>${__("Strength")}</th><th>${__("CPI")}</th>
			</tr></thead>
			<tbody>${rows.map((r) => `
				<tr>
					<td><a href="/app/force-arrangement/${encodeURIComponent(r.name)}">${r.name_div || r.name}</a></td>
					<td>${r.size_div || "-"}</td>
					<td>${r.current_posture || "-"}</td>
					<td>${r.strength_pct || 0}%</td>
					<td>${r.combat_power_index || 0}</td>
				</tr>`).join("")}
			</tbody>
		</table>`;
	frappe.msgprint({ title: __("Sub-units of {0}", [title]), message: html, wide: true });
}
