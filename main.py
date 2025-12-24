import argparse
from pathlib import Path
import yaml
import logging

from collectors.process_collector import collect_one_process_event
from collectors.network_collector import collect_network_snapshot
from collectors.persistence_collector import collect_persistence_snapshot
from collectors.system_metadata import collect_system_snapshot

from storage.writer import write_events, read_all, DEFAULT_DATA_PATH

from analyzer.baseline import BaselineAnalyzer
from analyzer.anomaly import AnomalyDetector
from analyzer.explain import ExplainabilityEngine
from normalizer.validator import validate_event, load_schema


def load_config(path: Path = Path("config.yaml")):
    with open(path, "r") as f:
        return yaml.safe_load(f)


COLLECTOR_REGISTRY = {
    "process": collect_one_process_event,
    "network": collect_network_snapshot,
    "persistence": collect_persistence_snapshot,
    "system_metadata": collect_system_snapshot,
}


def collect_enabled_events(cfg):
    enabled = cfg.get("collectors", {}).get("enabled", [])
    events = []
    schema = load_schema()
    for name in enabled:
        func = COLLECTOR_REGISTRY.get(name)
        if not func:
            continue
        try:
            ev = func()
            if ev:
                ok, msg = validate_event(ev, schema)
                if not ok:
                    logging.warning(f"Validation failed for {name}: {msg}")
                else:
                    events.append(ev)
        except Exception as e:
            # Skip failing collectors to keep pipeline robust
            logging.warning(f"collector '{name}' failed: {e}")
    return events


def build_report_md(baseline, anomalies, explanations):
    lines = []
    lines.append("# Telemetry Report")
    lines.append("")
    lines.append("## Baseline Summary")
    lines.append(f"- Event types: {baseline.get('event_type_counts', {})}")
    lines.append(f"- Top processes: {baseline.get('top_processes', [])}")
    lines.append(f"- Net established avg: {baseline.get('net_established_avg', 0):.2f}")
    lines.append(f"- Persistence count avg: {baseline.get('persistence_count_avg', 0):.2f}")
    lines.append("")
    lines.append("## Anomalies")
    lines.append(f"- Count: {len(anomalies)}")
    for exp in explanations:
        lines.append(f"- {exp.get('summary')}")
    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Telemetry App")
    parser.add_argument("--once", action="store_true", help="Run a single collection/analyze cycle")
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    parser.add_argument("--log", default="INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR)")
    args = parser.parse_args()

    cfg = load_config(Path(args.config))

    logging.basicConfig(level=getattr(logging, args.log.upper(), logging.INFO), format="%(levelname)s %(message)s")

    data_path = Path(cfg.get("storage", {}).get("path", str(DEFAULT_DATA_PATH)))

    # Collect
    events = collect_enabled_events(cfg)
    if events:
        write_events(events, data_path=data_path)
        print(f"✔ {len(events)} telemetry events written to {data_path}")
    else:
        print("ℹ No events collected")

    # Analyze over all stored data
    all_events = read_all(data_path=data_path)
    baseline = BaselineAnalyzer().fit(all_events).summary()
    detector = AnomalyDetector(
        net_multiplier=cfg.get("analyzer", {}).get("net_multiplier", 3.0),
        persistence_multiplier=cfg.get("analyzer", {}).get("persistence_multiplier", 3.0),
    )
    anomalies = detector.detect(all_events, baseline)
    explanations = ExplainabilityEngine().explain(anomalies)

    # Output report
    report_path = Path(cfg.get("output", {}).get("report_path", "output/report.md"))
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as f:
        f.write(build_report_md(baseline, anomalies, explanations))
    print(f"✔ Report written to {report_path}")

    if not args.once:
        print("ℹ '--once' run complete. For scheduling, integrate a timer or launchd.")


if __name__ == "__main__":
    main()
