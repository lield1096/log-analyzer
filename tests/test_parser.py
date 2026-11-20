from datetime import datetime

import pytest

from log_analyzer.models import Severity
from log_analyzer.parser import parse_files, parse_line, parse_lines


def test_parses_standard_line():
    entry = parse_line("2026-11-01 08:00:00 ERROR [db] Connection lost", file="a.log", line_number=3)
    assert entry is not None
    assert entry.timestamp == datetime(2026, 11, 1, 8, 0, 0)
    assert entry.severity is Severity.ERROR
    assert entry.source == "db"
    assert entry.message == "Connection lost"
    assert (entry.file, entry.line_number) == ("a.log", 3)


def test_source_is_optional():
    entry = parse_line("2026-11-01 08:00:00 INFO Service started")
    assert entry is not None
    assert entry.source is None
    assert entry.message == "Service started"


@pytest.mark.parametrize(
    "line, expected",
    [
        ("2026-11-01 08:00:00,123 [WARN] Disk almost full", Severity.WARNING),
        ("2026-11-01T08:00:00.123Z CRITICAL Out of memory", Severity.ERROR),
        ("2026-11-01 08:00:00 fatal [core] Panic", Severity.ERROR),
        ("2026-11-01 08:00:00 info [core] lowercase level", Severity.INFO),
    ],
)
def test_accepts_common_variants(line, expected):
    entry = parse_line(line)
    assert entry is not None
    assert entry.severity is expected


@pytest.mark.parametrize(
    "line",
    [
        "",
        "Traceback (most recent call last):",
        "2026-11-01 08:00:00 DEBUG [cache] noisy",
        "not a log line at all",
    ],
)
def test_unrecognised_lines_return_none(line):
    assert parse_line(line) is None


def test_parse_lines_counts_skipped():
    result = parse_lines(
        [
            "2026-11-01 08:00:00 INFO ok\n",
            "  stack frame\n",
            "\n",  # blank lines are ignored entirely
            "2026-11-01 08:00:01 ERROR bad\n",
        ]
    )
    assert len(result.entries) == 2
    assert result.skipped_lines == 1


def test_parse_files_merges_and_sorts(tmp_path):
    later = tmp_path / "later.log"
    earlier = tmp_path / "earlier.log"
    later.write_text("2026-11-02 00:00:00 INFO second\n")
    earlier.write_text("2026-11-01 00:00:00 INFO first\n")

    result = parse_files([later, earlier])

    assert [e.message for e in result.entries] == ["first", "second"]
    assert result.files == [str(later), str(earlier)]


def test_parse_sample_fixture(sample_log):
    result = parse_files([sample_log])
    assert len(result.entries) == 7
    assert result.skipped_lines == 3  # 2 traceback lines + 1 DEBUG line
