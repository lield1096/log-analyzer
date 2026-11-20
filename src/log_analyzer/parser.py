"""Turn raw log lines into :class:`LogEntry` objects.

The expected line format is the one used by most application loggers::

    2026-11-03 14:22:07 ERROR [payments] Payment 4821 failed: card declined
    2026-11-03 14:22:07,512 [WARN] Disk usage at 91%

That is: a timestamp, a severity (optionally in brackets), an optional
``[source]`` tag, and the message. Lines that don't match (stack traces,
blank lines, DEBUG output) are counted as skipped rather than raising.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .models import LogEntry, Severity

LINE_PATTERN = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2})(?:[.,]\d+)?Z?\s+"
    r"\[?(?P<severity>[A-Za-z]+)\]?\s+"
    r"(?:\[(?P<source>[^\]]+)\]\s+)?"
    r"(?P<message>.*)$"
)


@dataclass
class ParseResult:
    """Entries parsed from one or more files, plus a count of skipped lines."""

    entries: list[LogEntry] = field(default_factory=list)
    skipped_lines: int = 0
    files: list[str] = field(default_factory=list)


def parse_line(line: str, file: str = "", line_number: int = 0) -> LogEntry | None:
    """Parse a single line. Returns ``None`` if the line isn't a recognised entry."""
    match = LINE_PATTERN.match(line.strip())
    if not match:
        return None

    try:
        severity = Severity.from_string(match["severity"])
    except ValueError:
        return None  # e.g. DEBUG or TRACE lines

    timestamp = datetime.strptime(match["timestamp"].replace("T", " "), "%Y-%m-%d %H:%M:%S")
    return LogEntry(
        timestamp=timestamp,
        severity=severity,
        message=match["message"].strip(),
        source=match["source"],
        file=file,
        line_number=line_number,
    )


def parse_lines(lines: Iterable[str], file: str = "") -> ParseResult:
    """Parse an iterable of lines (e.g. an open file)."""
    result = ParseResult(files=[file] if file else [])
    for number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        entry = parse_line(line, file=file, line_number=number)
        if entry is None:
            result.skipped_lines += 1
        else:
            result.entries.append(entry)
    return result


def parse_files(paths: Iterable[str | Path]) -> ParseResult:
    """Parse several log files into one combined, time-ordered result."""
    combined = ParseResult()
    for path in paths:
        path = Path(path)
        with path.open(encoding="utf-8", errors="replace") as handle:
            result = parse_lines(handle, file=str(path))
        combined.entries.extend(result.entries)
        combined.skipped_lines += result.skipped_lines
        combined.files.append(str(path))
    combined.entries.sort(key=lambda e: e.timestamp)
    return combined
