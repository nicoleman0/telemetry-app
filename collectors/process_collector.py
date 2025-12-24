import psutil
from datetime import datetime
import subprocess
import shlex
from collectors.system_metadata import get_system_metadata

def collect_one_process_event():
    for proc in psutil.process_iter(attrs=["pid", "ppid", "name", "exe", "username", "cmdline"]):
        info = proc.info
        signed, team_id = _codesign_info(info.get("exe"))
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
                "signed": signed,
                "team_id": team_id
            },
            "network": {},
            "persistence": {},
            "risk": {
                "score": 0,
                "reasons": []
            }
        }


def _codesign_info(path):
    if not path:
        return None, None
    try:
        # Use codesign to check signing and extract TeamIdentifier if available
        cmd = f"/usr/bin/codesign -dv --verbose=4 {shlex.quote(path)}"
        proc = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=2)
        output = proc.stderr or proc.stdout
        signed = "is signed" in output or "Authority=" in output
        team_id = None
        for line in output.splitlines():
            if line.strip().startswith("TeamIdentifier="):
                team_id = line.strip().split("=", 1)[-1]
                break
        return signed, team_id
    except Exception:
        return None, None
