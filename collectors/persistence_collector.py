import os
from datetime import datetime
from collectors.system_metadata import get_system_metadata


LAUNCH_AGENT_DIRS = [
	os.path.expanduser("~/Library/LaunchAgents"),
	"/Library/LaunchAgents",
	"/Library/LaunchDaemons",
]


def _list_plists(paths):
	items = []
	for p in paths:
		if not os.path.isdir(p):
			continue
		for name in os.listdir(p):
			if name.endswith(".plist"):
				items.append({
					"name": name,
					"path": os.path.join(p, name),
				})
	return items


def collect_persistence_snapshot():
	"""Return a single persistence telemetry event summarizing common macOS persistence locations."""
	plists = _list_plists(LAUNCH_AGENT_DIRS)
	return {
		"timestamp": datetime.now().isoformat() + "Z",
		"host": get_system_metadata(),
		"event": {
			"type": "persistence_snapshot",
			"source": "persistence_collector",
		},
		"persistence": {
			"launch_items": plists,
			"count": len(plists),
		},
		"process": {},
		"network": {},
		"risk": {
			"score": 0,
			"reasons": [],
		},
	}

