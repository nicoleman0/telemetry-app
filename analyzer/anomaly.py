class AnomalyDetector:
	"""Simple threshold-based anomaly detector using baseline summary."""

	def __init__(self, net_multiplier=3.0, persistence_multiplier=3.0):
		self.net_multiplier = net_multiplier
		self.persistence_multiplier = persistence_multiplier

	def detect(self, events, baseline_summary):
		anomalies = []
		net_avg = baseline_summary.get("net_established_avg", 0) or 0
		pers_avg = baseline_summary.get("persistence_count_avg", 0) or 0

		for ev in events:
			net = ev.get("network", {})
			persistence = ev.get("persistence", {})
			reasons = []

			if "established" in net and net_avg > 0:
				if net["established"] > self.net_multiplier * net_avg:
					reasons.append(f"Established conns {net['established']} > {self.net_multiplier}x baseline ({net_avg:.2f})")

			if "count" in persistence and pers_avg > 0:
				if persistence["count"] > self.persistence_multiplier * pers_avg:
					reasons.append(f"Persistence items {persistence['count']} > {self.persistence_multiplier}x baseline ({pers_avg:.2f})")

			if reasons:
				ev = dict(ev)  # shallow copy
				ev.setdefault("risk", {"score": 0, "reasons": []})
				ev["risk"]["score"] = min(100, 50 + 10 * len(reasons))
				ev["risk"]["reasons"].extend(reasons)
				anomalies.append(ev)

		return anomalies

