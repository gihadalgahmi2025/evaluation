# Copyright (c) 2026, Aljahmi and contributors
# For license information, please see license.txt
"""Backwards compatible facade over :mod:`evaluation.workspace_builder`.

Charts and number cards are declared together with their workspace (in
``workspace_builder.WORKSPACE_SPECS``); this module exposes the subset needed
by ``setup.create_dashboards`` and by ``bench execute``.
"""

from __future__ import annotations

from evaluation.workspace_builder import (
	build_charts_and_cards,
	build_dashboards,
	build_number_cards,
	build_workspaces,
)

__all__ = [
	"build_charts_and_cards",
	"build_dashboards",
	"build_number_cards",
	"build_workspaces",
]
