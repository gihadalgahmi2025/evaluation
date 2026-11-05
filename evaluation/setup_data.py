# Copyright (c) 2026, Aljahmi and contributors
# For license information, please see license.txt
"""Static bootstrap data shipped with the Evaluation app.

Keeping the data here (instead of scattering literals inside ``setup.py``)
makes it easy to review, translate and extend.
"""

# ---------------------------------------------------------------------------
# Roles: (name, description, desk_access)
# ---------------------------------------------------------------------------
DEFAULT_ROLES = [
	("Evaluation User", "Read and create reconnaissance data for assigned units", 1),
	("Evaluation Manager", "Full control over evaluation data of all units", 1),
	("Evaluation Commander", "Approve operations, targets and score cards", 1),
	("Evaluation Intel Officer", "Create intel reports, review sources and targets", 1),
	("Evaluation Ops Officer", "Manage operations orders, phases and tasks", 1),
	("Evaluation Fires Officer", "Manage fire support units and target nominations", 1),
	("Evaluation Logistics Officer", "Manage supply classes, ammunition and readiness", 1),
]

# ---------------------------------------------------------------------------
# Workflows
# ---------------------------------------------------------------------------
def _state(state, doc_status, allow_edit):
	return {"state": state, "doc_status": doc_status, "allow_edit": allow_edit}


def _transition(action, state, next_state, allowed, condition=None):
	row = {
		"action": action,
		"state": state,
		"next_state": next_state,
		"allowed": allowed,
	}
	return row


_INTEL_FLOW_STATES = [
	_state("Draft", "0", "Evaluation User"),
	_state("Pending Review", "0", "Evaluation User"),
	_state("Validated", "0", "Evaluation Intel Officer"),
	_state("Approved", "1", "Evaluation Manager"),
	_state("Rejected", "0", "Evaluation Manager"),
	_state("Closed", "1", "Evaluation Manager"),
]

_INTEL_FLOW_TRANSITIONS = [
	_transition("Submit for Review", "Draft", "Pending Review", "Evaluation User"),
	_transition("Validate", "Pending Review", "Validated", "Evaluation Intel Officer"),
	_transition("Approve", "Validated", "Approved", "Evaluation Manager"),
	_transition("Reject", "Pending Review", "Rejected", "Evaluation Intel Officer"),
	_transition("Reopen", "Rejected", "Draft", "Evaluation Manager"),
	_transition("Close", "Approved", "Closed", "Evaluation Manager"),
]

_OPERATIONS_STATES = [
	_state("Draft", "0", "Evaluation Ops Officer"),
	_state("Pending Review", "0", "Evaluation Ops Officer"),
	_state("Approved", "1", "Evaluation Commander"),
	_state("Active", "1", "Evaluation Ops Officer"),
	_state("Rejected", "0", "Evaluation Commander"),
	_state("Closed", "1", "Evaluation Commander"),
]

_OPERATIONS_TRANSITIONS = [
	_transition("Submit for Review", "Draft", "Pending Review", "Evaluation Ops Officer"),
	_transition("Approve", "Pending Review", "Approved", "Evaluation Commander"),
	_transition("Activate", "Approved", "Active", "Evaluation Ops Officer"),
	_transition("Reject", "Pending Review", "Rejected", "Evaluation Commander"),
	_transition("Reopen", "Rejected", "Draft", "Evaluation Commander"),
	_transition("Close", "Active", "Closed", "Evaluation Commander"),
]

_TARGET_STATES = [
	_state("Draft", "0", "Evaluation Intel Officer"),
	_state("Validated", "0", "Evaluation Intel Officer"),
	_state("Approved", "1", "Evaluation Commander"),
	_state("Rejected", "0", "Evaluation Commander"),
	_state("Closed", "1", "Evaluation Commander"),
]

_TARGET_TRANSITIONS = [
	_transition("Validate", "Draft", "Validated", "Evaluation Intel Officer"),
	_transition("Approve", "Validated", "Approved", "Evaluation Commander"),
	_transition("Reject", "Validated", "Rejected", "Evaluation Commander"),
	_transition("Reopen", "Rejected", "Draft", "Evaluation Commander"),
	_transition("Close", "Approved", "Closed", "Evaluation Commander"),
]

WORKFLOWS = [
	{
		"workflow_name": "Daily Activity Review",
		"document_type": "Daily Activities",
		"states": _INTEL_FLOW_STATES,
		"transitions": _INTEL_FLOW_TRANSITIONS,
	},
	{
		"workflow_name": "Intel Report Review",
		"document_type": "Intel Report",
		"states": _INTEL_FLOW_STATES,
		"transitions": _INTEL_FLOW_TRANSITIONS,
	},
	{
		"workflow_name": "Target Approval",
		"document_type": "Target",
		"states": _TARGET_STATES,
		"transitions": _TARGET_TRANSITIONS,
	},
	{
		"workflow_name": "Operation Order Approval",
		"document_type": "Operation Order",
		"states": _OPERATIONS_STATES,
		"transitions": _OPERATIONS_TRANSITIONS,
	},
	{
		"workflow_name": "Situation Report Review",
		"document_type": "Situation Report",
		"states": _INTEL_FLOW_STATES,
		"transitions": _INTEL_FLOW_TRANSITIONS,
	},
	{
		"workflow_name": "Threat Assessment Review",
		"document_type": "Threat Assessment",
		"states": _INTEL_FLOW_STATES,
		"transitions": _INTEL_FLOW_TRANSITIONS,
	},
]

# ---------------------------------------------------------------------------
# Reference tables
# ---------------------------------------------------------------------------
COMBAT_POSTURES = [
	("Attack", "Offensive posture, unit is advancing", 1, 100, "Tactic", "#d32f2f", "ATK", 10),
	("Defend", "Defensive posture, unit holds ground", 1, 100, "Geographic", "#1565c0", "DEF", 20),
	("Delay", "Trading space for time", 1, 85, "Geographic", "#6a1b9a", "DLY", 30),
	("Withdraw", "Disengaging towards rear areas", 1, 60, "Geographic", "#4e342e", "WDR", 40),
	("Reserve", "Held back for future commitment", 1, 90, "Management", "#2e7d32", "RES", 50),
	("Reorganize", "Rebuilding combat power", 1, 70, "Management", "#f9a825", "RGN", 60),
	("Consolidate", "Securing gains after operations", 1, 80, "Management", "#00838f", "CNS", 70),
	("Ambush", "Prepared ambush position", 1, 95, "Tactic", "#c62828", "AMB", 80),
	("Screen", "Screening force covering a main body", 1, 75, "Tactic", "#455a64", "SCR", 90),
	("Guard", "Guard force securing a flank", 1, 75, "Tactic", "#37474f", "GRD", 100),
	("Unlocated", "Position unknown, presumed relocated", 1, 40, "Management", "#757575", "UNL", 110),
]

READINESS_METRICS = [
	("Personnel Strength", "Personnel", 10),
	("Equipment Serviceability", "Equipment", 20),
	("Ammunition Stocks", "Equipment", 30),
	("Fuel Reserves", "General", 40),
	("Medical Support", "Personnel", 50),
	("Command and Control", "General", 60),
	("Training Level", "Personnel", 70),
	("Logistics Pipeline", "General", 80),
	("Communications Integrity", "Equipment", 90),
	("Mobility / Transport", "Equipment", 100),
]

SUPPLY_CLASSES = [
	("Class I - Subsistence", "I", 10),
	("Class II - Clothing & Individual Equipment", "II", 20),
	("Class III - POL (Fuel & Lubricants)", "III", 30),
	("Class IV - Construction Materials", "IV", 40),
	("Class V - Ammunition", "V", 50),
	("Class VI - Personal Demand Items", "VI", 60),
	("Class VII - Major End Items", "VII", 70),
	("Class VIII - Medical Supplies", "VIII", 80),
	("Class IX - Repair Parts", "IX", 90),
	("Class X - Non-Military Programs", "X", 100),
]

#: The order of battle echelon ladder shared by Division Size and unit types
ECHELONS = [
	("Team", 10), ("Squad", 20), ("Platoon", 30), ("Company", 40), ("Battalion", 50),
	("Regiment", 60), ("Brigade", 70), ("Division", 80), ("Corps", 90),
	("Army", 100), ("Army Group", 110), ("Theatre Command", 120),
]

UNIT_TYPES = [
	("Infantry", 10), ("Mechanized Infantry", 20), ("Armoured", 30), ("Artillery", 40),
	("Air Defence", 50), ("Engineer", 60), ("Signal", 70), ("Logistics", 80),
	("Medical", 90), ("Military Police", 100), ("Special Forces", 110),
	("Reconnaissance", 120), ("Chemical", 130), ("Aviation", 140), ("Naval", 150),
]

FIRE_SUPPORT_TYPES = [
	("Mortar 60mm", 10), ("Mortar 81mm", 20), ("Mortar 120mm", 30),
	("Artillery 122mm", 40), ("Artillery 130mm", 50), ("Artillery 152mm", 60),
	("Artillery 155mm", 70), ("Multiple Launch Rocket System", 80),
	("Anti-Tank Guided Missile", 90), ("Air Defence Gun", 100),
	("Air Defence Missile", 110), ("Unmanned Aerial System", 120),
]

TARGET_CATEGORIES = [
	("Command and Control", 1), ("Logistics and Sustainment", 1), ("Manoeuvre Forces", 1),
	("Fire Support", 1), ("Air Defence", 1), ("Infrastructure", 1), ("Energy", 1),
	("Communications", 1), ("Transportation", 1), ("Personnel Concentrations", 1),
]

TARGET_TYPES = [
	("Headquarters", 10, 0), ("Command Post", 20, 1), ("Ammunition Depot", 30, 0),
	("Fuel Depot", 40, 0), ("Supply Point", 50, 0), ("Bridge", 60, 0),
	("Tunnel", 70, 0), ("Radar Site", 80, 1), ("Air Defence Battery", 90, 1),
	("Artillery Battery", 100, 0), ("Vehicle Park", 110, 0), ("Troop Concentration", 120, 1),
	("Communications Node", 130, 0), ("Power Station", 140, 0), ("Water Treatment Plant", 150, 0),
	("Airfield", 160, 0), ("Port", 170, 0), ("Missile Launcher", 180, 1),
]

COMBAT_EFFECTIVENESS_TYPES = [
	("Manning Level", "Combat", 10),
	("Weapons Serviceability", "Combat", 20),
	("Equipment Availability", "Combat", 30),
	("Mobility", "Combat", 40),
	("Command and Control", "Combat", 50),
	("Communications", "Combat", 60),
	("Morale", "Spiritual", 70),
	("Discipline", "Spiritual", 80),
	("Leadership Quality", "Spiritual", 90),
	("Training Proficiency", "Spiritual", 100),
	("Logistics Support", "Other", 110),
	("Medical Support", "Other", 120),
	("Intelligence Support", "Other", 130),
	("Engineering Support", "Other", 140),
]

COMBAT_POWER_WEIGHTS = [
	("readiness", 0.35, "Weight of readiness metrics in the combat power index"),
	("logistics", 0.25, "Weight of sustainment factors"),
	("ammunition", 0.20, "Weight of ammunition availability"),
	("strength", 0.20, "Weight of personnel and equipment strength"),
]

#: master lookups used by the recon documents
BOOTSTRAP_LIGHT = {
	"Division Size": [{"size_div": e, "sort_order": o} for e, o in ECHELONS],
	"Division Type": [{"type_div": e} for e, _ in UNIT_TYPES],
	"Fire Support Unit Type": [
		{"unit_name": name, "sort_order": order} for name, order in FIRE_SUPPORT_TYPES
	],
	"Supply Class": [
		{"class_name": name, "class_code": code, "sort_order": order}
		for name, code, order in SUPPLY_CLASSES
	],
	"Target Category": [{"category_name": name, "is_group": g} for name, g in TARGET_CATEGORIES],
	"Target Type": [
		{"type_name": name, "sort_order": order, "is_tst": tst}
		for name, order, tst in TARGET_TYPES
	],
}


#: military ranks, lowest -> highest (Arabic army convention)
MILITARY_RANKS = [
	("Soldier", 10), ("Corporal", 20), ("Sergeant", 30), ("Staff Sergeant", 40),
	("Warrant Officer", 50), ("Second Lieutenant", 60), ("First Lieutenant", 70),
	("Captain", 80), ("Major", 90), ("Lieutenant Colonel", 100), ("Colonel", 110),
	("Brigadier General", 120), ("Major General", 130), ("Lieutenant General", 140),
	("General", 150), ("Field Marshal", 160),
]

#: evaluation branches (service arms)
EVALUATION_BRANCHES = [
	("General Staff", 10), ("Operations", 20), ("Intelligence", 30),
	("Logistics", 40), ("Personnel", 50), ("Training", 60),
	("Engineering", 70), ("Medical Corps", 80), ("Signals", 90),
]

#: common activity sides used by the recon documents
ACTIVITY_SIDES = [
	"Ground Recon", "Aerial Recon", "Technical Collection", "Human Source Network",
	"Open Source Monitoring", "Border Observation",
]

#: supply / support reference numbers used across the reports
EVALUATION_DESIGNATIONS = [
	("Intelligence Analyst", 10), ("Operations Officer", 20), ("Targeteer", 30),
	("Logistics Officer", 40), ("Reconnaissance Controller", 50),
]


BOOTSTRAP_DOCS = {
	**BOOTSTRAP_LIGHT,
	"Combat Posture": [
		{
			"posture_name": name,
			"description": desc,
			"affects_readiness": affects,
			"readiness_modifier": modifier,
			"default_spread_type": spread,
			"map_color": color,
			"symbol_code": symbol,
			"sort_order": order,
		}
		for name, desc, affects, modifier, spread, color, symbol, order in COMBAT_POSTURES
	],
	"Readiness Metric": [
		{"metric_name": name, "item_group": group, "sort_order": order, "is_active": 1}
		for name, group, order in READINESS_METRICS
	],
	"Combat Effectiveness Type": [
		{"type_combat_effectiveness": name, "factor_group": group, "sort_order": order,
		 "is_active": 1}
		for name, group, order in COMBAT_EFFECTIVENESS_TYPES
	],
	"Combat Power Weight": [
		{"factor": factor, "weight": weight, "description": desc}
		for factor, weight, desc in COMBAT_POWER_WEIGHTS
	],
	"Military Rank": [{"rank_name": name} for name, _order in MILITARY_RANKS],
	"Evaluation Branch": [{"branch": name} for name, _order in EVALUATION_BRANCHES],
	"Evaluation Designation": [{"designation_name": name} for name, _order in EVALUATION_DESIGNATIONS],
}
