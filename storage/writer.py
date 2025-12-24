import json
from pathlib import Path

DEFAULT_DATA_PATH = Path("data/telemetry.jsonl")


def _ensure_parent(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)


def write_event(event: dict, data_path: Path = DEFAULT_DATA_PATH):
    _ensure_parent(data_path)
    with open(data_path, "a") as f:
        f.write(json.dumps(event) + "\n")


def write_events(events, data_path: Path = DEFAULT_DATA_PATH):
    _ensure_parent(data_path)
    with open(data_path, "a") as f:
        for ev in events:
            f.write(json.dumps(ev) + "\n")


def read_all(data_path: Path = DEFAULT_DATA_PATH):
    if not data_path.exists():
        return []
    events = []
    with open(data_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                # skip malformed line
                continue
    return events
