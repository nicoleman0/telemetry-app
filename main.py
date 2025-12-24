import argparse
from pathlib import Path
import yaml
import logging
import time
import zipfile
from datetime import datetime
from typing import Optional

from collectors.process_collector import collect_one_process_event
from collectors.network_collector import collect_network_snapshot
from collectors.persistence_collector import collect_persistence_snapshot
from collectors.system_metadata import collect_system_snapshot

from storage.writer import write_events, read_all, DEFAULT_DATA_PATH

from analyzer.baseline import BaselineAnalyzer
from analyzer.anomaly import AnomalyDetector
from analyzer.explain import ExplainabilityEngine
from normalizer.validator import validate_event, load_schema
from jinja2 import Environment, FileSystemLoader, select_autoescape


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


def build_report_html(baseline, anomalies, explanations, events):
    try:
        templates_dir = Path("output/templates")
        env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=select_autoescape(["html", "xml"]),
        )
        tmpl = env.get_template("report.html.j2")
        return tmpl.render(baseline=baseline, anomalies=anomalies, explanations=explanations, events=events)
    except Exception as e:
        logging.warning(f"HTML report generation failed: {e}")
        return ""


def main():
    parser = argparse.ArgumentParser(description="Telemetry App")
    parser.add_argument("--once", action="store_true", help="Run a single collection/analyze cycle")
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    parser.add_argument("--log", default="INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR)")
    parser.add_argument("--interval", type=int, help="Seconds between collection cycles (overrides config)")
    parser.add_argument("--max-cycles", type=int, default=0, help="Maximum cycles to run (0 = unlimited)")
    parser.add_argument("--zip", action="store_true", help="Bundle reports into a ZIP after each cycle")
    parser.add_argument("--zip-path", help="Override zip output path")
    args = parser.parse_args()

    cfg = load_config(Path(args.config))

    logging.basicConfig(level=getattr(logging, args.log.upper(), logging.INFO), format="%(levelname)s %(message)s")

    def run_cycle():
        data_path = Path(cfg.get("storage", {}).get("path", str(DEFAULT_DATA_PATH)))

        # Collect
        events = collect_enabled_events(cfg)
        if events:
            write_events(events, data_path=data_path)
            logging.info(f"{len(events)} telemetry events written to {data_path}")
        else:
            logging.info("No events collected")

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
        logging.info(f"Report written to {report_path}")

        html_path = Path(cfg.get("output", {}).get("html_path", "output/report.html"))
        html = build_report_html(baseline, anomalies, explanations, all_events)
        if html:
            html_path.parent.mkdir(parents=True, exist_ok=True)
            with open(html_path, "w") as f:
                f.write(html)
            logging.info(f"HTML report written to {html_path}")

        # Optional zip bundling
        zip_enabled = args.zip or bool(cfg.get("output", {}).get("zip_enabled", False))
        zip_path_override = args.zip_path if args.zip_path else cfg.get("output", {}).get("zip_path")
        bundle_reports(report_path, html_path, zip_enabled, Path(zip_path_override) if zip_path_override else None)

def bundle_reports(md_path: Path, html_path: Path, zip_enabled: bool, zip_path: Optional[Path]):
    if not zip_enabled:
        return
    if zip_path is None:
        zip_path = Path("output/report_bundle.zip")
    try:
        zip_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
            if md_path.exists():
                z.write(md_path, arcname=md_path.name)
            if html_path.exists():
                z.write(html_path, arcname=html_path.name)
            # add a small manifest
            manifest = f"generated_at={datetime.now().isoformat()}Z\nfiles={md_path.name},{html_path.name}\n"
            z.writestr("manifest.txt", manifest)
        logging.info(f"ZIP bundle written to {zip_path}")
    except Exception as e:
        logging.warning(f"ZIP bundling failed: {e}")

    # Determine scheduling
    interval = args.interval if args.interval is not None else cfg.get("collectors", {}).get("interval_seconds")
    max_cycles = args.max_cycles

    # If --once or no interval value, run a single cycle
    if args.once or not interval:
        run_cycle()
        logging.info("One-shot run complete")
        return

    # Scheduled loop
    logging.info(f"Starting scheduled collection every {interval} seconds")
    cycles_done = 0
    try:
        while True:
            run_cycle()
            cycles_done += 1
            if max_cycles and cycles_done >= max_cycles:
                logging.info("Reached max cycles; exiting")
                break
            time.sleep(interval)
    except KeyboardInterrupt:
        logging.info("Interrupted by user; exiting")


if __name__ == "__main__":
    main()
