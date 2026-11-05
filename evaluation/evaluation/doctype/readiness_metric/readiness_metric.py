# Copyright (c) 2026, Aljahmi and contributors
# For license information, please see license.txt
from evaluation.evaluation.mixins import MasterRecord


class ReadinessMetric(MasterRecord):
	"""Controller for Readiness Metric."""

	title_field = "metric_name"
