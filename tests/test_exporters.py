import csv
import json

from log_analyzer.analyzer import analyze
from log_analyzer.exporters import CSV_COLUMNS, export_csv, export_json
from log_analyzer.parser import parse_files


def _result(sample_log):
    parsed = parse_files([sample_log])
    return analyze(parsed.entries, files=parsed.files, skipped_lines=parsed.skipped_lines)


def test_export_json(sample_log, tmp_path):
    out = export_json(_result(sample_log), tmp_path / "nested" / "report.json")

    data = json.loads(out.read_text())
    assert data["total_entries"] == 7
    assert data["skipped_lines"] == 3
    assert data["counts"] == {"ERROR": 4, "WARNING": 1, "INFO": 2}
    assert data["time_range"] == {"start": "2026-11-01 08:00:00", "end": "2026-11-03 14:00:00"}
    assert data["recurring_errors"][0]["count"] == 3
    assert data["recurring_errors"][0]["sources"] == ["db"]


def test_export_csv(sample_log, tmp_path):
    out = export_csv(_result(sample_log), tmp_path / "errors.csv")

    with out.open(newline="") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == CSV_COLUMNS
        rows = list(reader)
    assert len(rows) == 1
    assert rows[0]["count"] == "3"
    assert rows[0]["signature"] == "Connection timeout after <N>ms to <IP>"
    assert rows[0]["first_seen"] == "2026-11-01 09:00:00"


def test_export_csv_with_no_errors_writes_header_only(tmp_path):
    out = export_csv(analyze([]), tmp_path / "empty.csv")
    assert out.read_text().strip() == ",".join(CSV_COLUMNS)
