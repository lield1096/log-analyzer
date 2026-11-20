from datetime import datetime

import pytest

from log_analyzer.filters import filter_entries, parse_date
from log_analyzer.models import LogEntry, Severity


def make(day: int, severity: Severity) -> LogEntry:
    return LogEntry(timestamp=datetime(2026, 11, day, 12, 0, 0), severity=severity, message="m")


ENTRIES = [
    make(1, Severity.INFO),
    make(2, Severity.WARNING),
    make(3, Severity.ERROR),
    make(4, Severity.ERROR),
]


def test_no_filters_returns_everything():
    assert filter_entries(ENTRIES) == ENTRIES


def test_filter_by_single_severity():
    result = filter_entries(ENTRIES, severities=[Severity.ERROR])
    assert [e.timestamp.day for e in result] == [3, 4]


def test_filter_by_multiple_severities():
    result = filter_entries(ENTRIES, severities=[Severity.ERROR, Severity.WARNING])
    assert len(result) == 3


def test_filter_by_date_range():
    result = filter_entries(ENTRIES, since=datetime(2026, 11, 2), until=datetime(2026, 11, 3, 23, 59, 59))
    assert [e.timestamp.day for e in result] == [2, 3]


def test_combined_filters():
    result = filter_entries(ENTRIES, severities=[Severity.ERROR], since=datetime(2026, 11, 4))
    assert [e.timestamp.day for e in result] == [4]


def test_parse_date_formats():
    assert parse_date("2026-11-03") == datetime(2026, 11, 3)
    assert parse_date("2026-11-03 14:30") == datetime(2026, 11, 3, 14, 30)
    assert parse_date("2026-11-03T14:30:15") == datetime(2026, 11, 3, 14, 30, 15)


def test_parse_date_end_of_day_includes_whole_day():
    assert parse_date("2026-11-03", end_of_day=True) == datetime(2026, 11, 3, 23, 59, 59)
    # An explicit time is respected as-is.
    assert parse_date("2026-11-03 10:00", end_of_day=True) == datetime(2026, 11, 3, 10, 0)


def test_parse_date_rejects_garbage():
    with pytest.raises(ValueError, match="Invalid date"):
        parse_date("yesterday")
