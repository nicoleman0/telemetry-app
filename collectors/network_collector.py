import psutil
from datetime import datetime
from collectors.system_metadata import get_system_metadata


def collect_network_snapshot():
	"""Return a single network telemetry event capturing IO counters and open connections summary."""
	io = psutil.net_io_counters()
	conns = psutil.net_connections(kind="inet")
	listening = sum(1 for c in conns if c.status == "LISTEN")
	established = sum(1 for c in conns if c.status == "ESTABLISHED")

	return {
		"timestamp": datetime.now().isoformat() + "Z",
		"host": get_system_metadata(),
		"event": {
			"type": "network_snapshot",
			"source": "network_collector",
		},
		"network": {
			"bytes_sent": io.bytes_sent,
			"bytes_recv": io.bytes_recv,
			"packets_sent": io.packets_sent,
			"packets_recv": io.packets_recv,
			"listening": listening,
			"established": established,
		},
		"process": {},
		"persistence": {},
		"risk": {
			"score": 0,
			"reasons": [],
		},
	}

