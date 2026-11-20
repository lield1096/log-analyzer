from datetime import datetime

import pytest

from log_analyzer.analyzer import analyze, group_errors, normalize_message
from log_analyzer.models import LogEntry, Severity
from log_analyzer.parser import parse_files


@pytest.mark.parametrize(
    "message, expected",
    [
        ("Timeout after 3000ms", "Timeout after <N>ms"),
        ("Cannot reach 10.0.0.12:5432", "Cannot reach <IP>"),
        ("Request 123e4567-e89b-12d3-a456-426614174000 failed", "Request <UUID> failed"),
        ("Bad pointer 0xDEADBEEF", "Bad pointer <HEX>"),
        ("Missing key 'customer_id'", "Missing key <STR>"),
        ("Mail to bob@example.com bounced", "Mail to <EMAIL> bounced"),
        ("No variable parts here", "No variable parts here"),
    ],
)
def test_normalize_message(message, expected):
    assert normalize_message(message) == expected


def error(message: str, hour: int, source: str = "db") -> LogEntry:
    return LogEntry(datetime(2026, 11, 1, hour), Severity.ERROR, message, source=source)


def test_group_errors_merges_similar_messages():
    entries = [
        error("Timeout after 3000ms", 1),
        error("Timeout after 5000ms", 2, source="api"),
        error("Timeout after 100ms", 3),
        error("Disk full", 4),
    ]
    groups = group_errors(entries, min_count=2)

    assert len(groups) == 1
    group = groups[0]
    assert group.signature == "Timeout after <N>ms"
    assert group.count == 3
    assert group.first_seen == datetime(2026, 11, 1, 1)
    assert group.last_seen == datetime(2026, 11, 1, 3)
    assert group.sources == ["db", "api"]
    assert group.example == "Timeout after 3000ms"


def test_group_errors_ignores_non_errors_and_respects_min_count():
    entries = [
        error("Disk full", 1),
        LogEntry(datetime(2026, 11, 1, 2), Severity.WARNING, "Disk full"),
    ]
    assert group_errors(entries, min_count=2) == []
    assert len(group_errors(entries, min_count=1)) == 1


def test_groups_sorted_by_count_then_first_seen():
    entries = [error("A", 5), error("B 1", 1), error("B 2", 2), error("A", 6), error("C", 0), error("C", 7)]
    groups = group_errors(entries, min_count=2)
    assert [g.signature for g in groups] == ["C", "B <N>", "A"]


def test_analyze_sample(sample_log):
    parsed = parse_files([sample_log])
    result = analyze(parsed.entries, files=parsed.files, skipped_lines=parsed.skipped_lines)

    assert result.total_entries == 7
    assert result.counts == {Severity.ERROR: 4, Severity.WARNING: 1, Severity.INFO: 2}
    assert result.start == datetime(2026, 11, 1, 8, 0, 0)
    assert result.end == datetime(2026, 11, 3, 14, 0, 0)
    assert len(result.recurring_errors) == 1
    assert result.recurring_errors[0].count == 3
    assert result.recurring_errors[0].signature == "Connection timeout after <N>ms to <IP>"


def test_analyze_empty():
    result = analyze([])
    assert result.total_entries == 0
    assert result.start is None and result.end is None
    assert result.recurring_errors == []
    assert result.to_dict()["counts"] == {"ERROR": 0, "WARNING": 0, "INFO": 0}
