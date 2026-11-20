"""Summarise entries and group recurring errors.

Recurring errors are detected by *normalising* each error message: variable
parts such as numbers, IDs, IP addresses and quoted values are replaced with
placeholders, so these two lines end up in the same group::

    Timeout after 3000ms calling 10.0.0.12 (request 8f1c...)
    Timeout after 5000ms calling 10.0.0.47 (request 2b9a...)
    -> Timeout after <N>ms calling <IP> (request <UUID>)
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime

from .models import LogEntry, Severity

# Order matters: more specific patterns must run before the generic number rule.
_NORMALIZERS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}\b", re.IGNORECASE), "<UUID>"),
    (re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b"), "<EMAIL>"),
    (re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}(?::\d+)?\b"), "<IP>"),
    (re.compile(r"\b0x[0-9a-fA-F]+\b"), "<HEX>"),
    (re.compile(r"'[^']*'|\"[^\"]*\""), "<STR>"),
    # Numbers not glued to a preceding word, so "3000ms" -> "<N>ms" but "v2" stays.
    (re.compile(r"(?<![\w.])\d+(?:\.\d+)?"), "<N>"),
]


def normalize_message(message: str) -> str:
    """Replace variable parts of a message with placeholders."""
    for pattern, placeholder in _NORMALIZERS:
        message = pattern.sub(placeholder, message)
    return message


@dataclass
class ErrorGroup:
    """A set of error entries sharing the same normalised message."""

    signature: str
    count: int
    first_seen: datetime
    last_seen: datetime
    example: str
    sources: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "signature": self.signature,
            "count": self.count,
            "first_seen": self.first_seen.isoformat(sep=" "),
            "last_seen": self.last_seen.isoformat(sep=" "),
            "sources": self.sources,
            "example": self.example,
        }


@dataclass
class AnalysisResult:
    """Everything the report and exporters need."""

    total_entries: int
    counts: dict[Severity, int]
    start: datetime | None
    end: datetime | None
    recurring_errors: list[ErrorGroup]
    files: list[str] = field(default_factory=list)
    skipped_lines: int = 0

    def to_dict(self) -> dict:
        return {
            "files": self.files,
            "total_entries": self.total_entries,
            "skipped_lines": self.skipped_lines,
            "time_range": {
                "start": self.start.isoformat(sep=" ") if self.start else None,
                "end": self.end.isoformat(sep=" ") if self.end else None,
            },
            "counts": {severity.value: self.counts.get(severity, 0) for severity in Severity},
            "recurring_errors": [group.to_dict() for group in self.recurring_errors],
        }


def group_errors(entries: Iterable[LogEntry], min_count: int = 2) -> list[ErrorGroup]:
    """Group ERROR entries by signature; keep groups seen at least ``min_count`` times.

    Groups are sorted by count (highest first), then by first occurrence.
    """
    groups: dict[str, ErrorGroup] = {}
    for entry in entries:
        if entry.severity is not Severity.ERROR:
            continue
        signature = normalize_message(entry.message)
        group = groups.get(signature)
        if group is None:
            group = ErrorGroup(
                signature=signature,
                count=0,
                first_seen=entry.timestamp,
                last_seen=entry.timestamp,
                example=entry.message,
            )
            groups[signature] = group
        group.count += 1
        group.first_seen = min(group.first_seen, entry.timestamp)
        group.last_seen = max(group.last_seen, entry.timestamp)
        if entry.source and entry.source not in group.sources:
            group.sources.append(entry.source)

    recurring = [g for g in groups.values() if g.count >= min_count]
    recurring.sort(key=lambda g: (-g.count, g.first_seen))
    return recurring


def analyze(
    entries: list[LogEntry],
    min_count: int = 2,
    files: list[str] | None = None,
    skipped_lines: int = 0,
) -> AnalysisResult:
    """Build an :class:`AnalysisResult` from (already filtered) entries."""
    counts = {severity: 0 for severity in Severity}
    for entry in entries:
        counts[entry.severity] += 1

    timestamps = [entry.timestamp for entry in entries]
    return AnalysisResult(
        total_entries=len(entries),
        counts=counts,
        start=min(timestamps) if timestamps else None,
        end=max(timestamps) if timestamps else None,
        recurring_errors=group_errors(entries, min_count=min_count),
        files=list(files or []),
        skipped_lines=skipped_lines,
    )
