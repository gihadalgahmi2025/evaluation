# Copyright (c) 2026, Aljahmi and contributors
# For license information, please see license.txt
"""Legacy desktop module listing (kept for compatibility with older benches).

Modern Frappe (v14+) builds the desk navigation from Workspace records, which
this app creates in ``evaluation.workspace_builder``.
"""

from frappe import _


def get_data():
	return [
		{
			"module_name": "Evaluation",
			"color": "#2490ef",
			"icon": "octicon octicon-checklist",
			"type": "module",
			"label": _("Evaluation"),
		},
		{
			"module_name": "Reconnaissance",
			"color": "#ff8f00",
			"icon": "octicon octicon-search",
			"type": "module",
			"label": _("Reconnaissance"),
		},
		{
			"module_name": "Order Of Battle",
			"color": "#e64a19",
			"icon": "octicon octicon-organization",
			"type": "module",
			"label": _("Order Of Battle"),
		},
		{
			"module_name": "Targeting",
			"color": "#43a047",
			"icon": "octicon octicon-crosshairs",
			"type": "module",
			"label": _("Targeting"),
		},
		{
			"module_name": "Operations",
			"color": "#6d4c41",
			"icon": "octicon octicon-milestone",
			"type": "module",
			"label": _("Operations"),
		},
		{
			"module_name": "Personnel",
			"color": "#0097a7",
			"icon": "octicon octicon-people",
			"type": "module",
			"label": _("Personnel"),
		},
	]
