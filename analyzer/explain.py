class ExplainabilityEngine:
	"""Generates simple explanations for anomaly events."""

	def explain(self, anomalies):
		explanations = []
		for ev in anomalies:
			risk = ev.get("risk", {})
			reasons = risk.get("reasons", [])
			event_type = ev.get("event", {}).get("type", "event")
			if reasons:
				explanations.append({
					"event_type": event_type,
					"summary": f"{event_type} flagged: " + "; ".join(reasons),
				})
		return explanations

