import psutil
from datetime import datetime
from collectors.system_metadata import get_system_metadata

def collect_one_process_event():
    for proc in psutil.process_iter(attrs=["pid", "ppid", "name", "exe", "username", "cmdline"]):
        info = proc.info
        return {
            "timestamp": datetime.now().isoformat() + "Z",
            "host": get_system_metadata(),
            "event": {
                "type": "process_snapshot",
                "source": "process_collector"
            },
            "process": {
                "pid": info.get("pid"),
                "ppid": info.get("ppid"),
                "name": info.get("name"),
                "path": info.get("exe"),
                "cmdline": info.get("cmdline"),
                "username": info.get("username"),
                "signed": None,
                "team_id": None
            },
            "network": {},
            "persistence": {},
            "risk": {
                "score": 0,
                "reasons": []
            }
        }
