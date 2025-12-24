import platform
import socket
from datetime import datetime


def get_system_metadata():
    return {
        "hostname": socket.gethostname(),
        "os": "macOS",
        "os_version": platform.mac_ver()[0],
        "architecture": platform.machine(),
    }


def collect_system_snapshot():
    meta = get_system_metadata()
    return {
        "timestamp": datetime.now().isoformat() + "Z",
        "host": meta,
        "event": {
            "type": "system_snapshot",
            "source": "system_metadata",
        },
        "process": {},
        "network": {},
        "persistence": {},
        "risk": {"score": 0, "reasons": []},
    }
