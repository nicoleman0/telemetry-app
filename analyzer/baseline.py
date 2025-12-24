from collections import Counter


class BaselineAnalyzer:
	"""Builds simple baselines across telemetry events for later anomaly detection."""

	def __init__(self):
		self.event_type_counts = Counter()
		self.process_name_counts = Counter()
		self.net_established_hist = []
		self.persistence_count_hist = []

	def fit(self, events):
		"""Compute baseline metrics from an iterable of events (dicts)."""
		for ev in events:
			et = ev.get("event", {}).get("type")
			if et:
				self.event_type_counts[et] += 1

			proc_name = (ev.get("process", {}).get("name") or "")
			if proc_name:
				self.process_name_counts[proc_name] += 1

			net = ev.get("network", {})
			if "established" in net:
				self.net_established_hist.append(net["established"]) 

			persistence = ev.get("persistence", {})
			if "count" in persistence:
				self.persistence_count_hist.append(persistence["count"]) 

		return self

	def summary(self):
		return {
			"event_type_counts": dict(self.event_type_counts),
			"top_processes": self.process_name_counts.most_common(10),
			"net_established_avg": (
				sum(self.net_established_hist) / len(self.net_established_hist)
				if self.net_established_hist else 0
			),
			"persistence_count_avg": (
				sum(self.persistence_count_hist) / len(self.persistence_count_hist)
				if self.persistence_count_hist else 0
			),
		}

