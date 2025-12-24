# Telemetry App (macOS)

A lightweight, pluggable telemetry scanner for macOS. It collects process, network, persistence, and system snapshots; normalizes and stores events; builds baselines; detects anomalies; and generates Markdown + HTML reports.

## Features
- Process snapshots with code signing (`signed`, `team_id`) via `codesign`
- Network IO + connection state summary (macOS-friendly fallback)
- Persistence discovery in LaunchAgents/Daemons
- JSONL storage (append-only) with read-back
- Baseline + simple anomaly detection and explanations
- Reports: Markdown and Jinja2-based HTML, optional ZIP bundling
- Configurable scheduling with `--interval` and `--max-cycles`

## Quick Start

### Requirements
- macOS
- Python 3.9+

### Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Run
- One-shot collection + report:
```bash
./.venv/bin/python main.py --once --log INFO
```
- Scheduled collection every 30s:
```bash
./.venv/bin/python main.py --interval 30 --log INFO
```
- Limit cycles (safe test):
```bash
./.venv/bin/python main.py --interval 5 --max-cycles 3 --log INFO
```
- Bundle reports into a ZIP:
```bash
./.venv/bin/python main.py --once --zip --log INFO
```

## Configuration
Edit [config.yaml](config.yaml):
- `collectors.enabled`: list of collectors to run (process, network, persistence, system_metadata)
- `collectors.interval_seconds`: default interval if `--interval` not provided
- `storage.type`: `jsonl` (SQLite optional future)
- `storage.path`: JSONL path (default `data/telemetry.jsonl`)
- `normalizer.schema_path`: path to schema (used by validator)
- `analyzer.net_multiplier`, `analyzer.persistence_multiplier`: anomaly thresholds
- `output.report_path`, `output.html_path`: report locations
- `output.zip_enabled`, `output.zip_path`: optional zip bundling

## Data & Reports
- Events: [data/telemetry.jsonl](data/telemetry.jsonl)
- Markdown: [output/report.md](output/report.md)
- HTML: [output/report.html](output/report.html)
- ZIP (if enabled): [output/report_bundle.zip](output/report_bundle.zip)

## Notes (macOS)
- `psutil.net_connections()` may require privileges; the network collector falls back gracefully.
- `codesign` is used to enrich process events; may be slow or unavailable for certain paths.

## Project Structure (high level)
- Collectors: [collectors/](collectors)
- Normalizer: [normalizer/](normalizer)
- Storage: [storage/](storage)
- Analyzer: [analyzer/](analyzer)
- Output: [output/](output)

## License
This project is licensed under the MIT License — see [LICENSE](LICENSE).
