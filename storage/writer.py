import json
from pathlib import Path

DATA_PATH = Path("data/telemetry.jsonl")

def write_event(event: dict):
    DATA_PATH.parent.mkdir(exist_ok=True)
    with open(DATA_PATH, "a") as f:
        f.write(json.dumps(event) + "\n")
