"""Filter parsed entries by severity and date range."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timedelta

from .models import LogEntry, Severity

_FORMATS = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d")


def parse_date(value: str, end_of_day: bool = False) -> datetime:
    """Parse a user-supplied date such as ``2026-11-03`` or ``2026-11-03 14:00``.

    With ``end_of_day=True`` a bare date expands to the last second of that day,
    so ``--until 2026-11-03`` includes everything logged on the 3rd.
    """
    value = value.strip()
    for fmt in _FORMATS:
        try:
            parsed = datetime.strptime(value, fmt)
        except ValueError:
            continue
        if end_of_day and fmt == "%Y-%m-%d":
            parsed += timedelta(days=1, seconds=-1)
        return parsed
    raise ValueError(f"Invalid date '{value}'. Use YYYY-MM-DD or 'YYYY-MM-DD HH:MM[:SS]'.")


def filter_entries(
    entries: Iterable[LogEntry],
    severities: Iterable[Severity] | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
) -> list[LogEntry]:
    """Keep entries matching all given criteria. ``None`` means "no restriction"."""
    wanted = set(severities) if severities else None
    result = []
    for entry in entries:
        if wanted is not None and entry.severity not in wanted:
            continue
        if since is not None and entry.timestamp < since:
            continue
        if until is not None and entry.timestamp > until:
            continue
        result.append(entry)
    return result
