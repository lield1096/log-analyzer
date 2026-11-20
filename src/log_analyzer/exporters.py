"""Write analysis results to JSON or CSV."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from .analyzer import AnalysisResult

CSV_COLUMNS = ["signature", "count", "first_seen", "last_seen", "sources", "example"]


def export_json(result: AnalysisResult, path: str | Path) -> Path:
    """Write the full analysis (summary + recurring errors) as pretty JSON."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result.to_dict(), indent=2) + "\n", encoding="utf-8")
    return path


def export_csv(result: AnalysisResult, path: str | Path) -> Path:
    """Write one row per recurring error group, ready for a spreadsheet."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for group in result.recurring_errors:
            row = group.to_dict()
            row["sources"] = ";".join(group.sources)
            writer.writerow(row)
    return path
