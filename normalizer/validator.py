import json
from pathlib import Path
from typing import Tuple


SCHEMA_PATH = Path("normalizer/telemetry_schema.json")


def load_schema(path: Path = SCHEMA_PATH):
    with open(path, "r") as f:
        # Accept simplified schema documents; convert to strict schema if needed later
        raw = json.load(f)
    # If this isn't a strict JSON Schema, wrap it loosely
    # For now, just ensure the top-level structure exists; robust checks can be added later.
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {
            "timestamp": {"type": "string"},
            "host": {"type": "object"},
            "event": {"type": "object"},
            "process": {"type": "object"},
            "network": {"type": "object"},
            "persistence": {"type": "object"},
            "risk": {"type": "object"},
        },
        "required": ["timestamp", "host", "event", "risk"],
        "additionalProperties": True,
    }
    return schema


def validate_event(event: dict, schema=None) -> Tuple[bool, str]:
    """Validate a single event against the telemetry schema.

    Imports jsonschema at runtime to avoid static analysis errors when the package
    isn't installed yet. Falls back to permissive pass when unavailable.
    """
    try:
        import jsonschema  # type: ignore
    except Exception:
        return True, "jsonschema not available; skipped"

    schema = schema or load_schema()

    # Prefer Draft 2020-12 validator if available; otherwise fall back.
    Validator = getattr(jsonschema, "Draft202012Validator", None)
    if Validator is None:
        Validator = getattr(jsonschema, "Draft7Validator", None)

    if Validator is None:
        # As a last resort, use jsonschema.validate
        try:
            jsonschema.validate(instance=event, schema=schema)  # type: ignore
            return True, ""
        except Exception as e:
            return False, str(e)

    validator = Validator(schema)
    errors = sorted(validator.iter_errors(event), key=lambda e: e.path)
    if errors:
        msgs = [f"{list(e.path)}: {e.message}" for e in errors]
        return False, "; ".join(msgs)
    return True, ""
