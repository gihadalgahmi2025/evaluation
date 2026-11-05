# Copyright (c) 2026, Aljahmi and contributors
# For license information, please see license.txt
from evaluation.evaluation.mixins import MasterRecord


class PublicActivity(MasterRecord):
	"""Controller for Public Activity."""

	title_field = "activity_name"
