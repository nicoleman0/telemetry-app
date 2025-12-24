import platform
import socket

def get_system_metadata():
    return {
        "hostname": socket.gethostname(),
        "os": "macOS",
        "os_version": platform.mac_ver()[0],
        "architecture": platform.machine()
    }
