import json
import subprocess
import sys
from pathlib import Path

import pytest
from rich.console import Console

from log_analyzer.cli import main

SAMPLES_DIR = Path(__file__).resolve().parent.parent / "samples"


def run(args):
    """Run the CLI in-process and return (exit_code, plain-text output)."""
    console = Console(record=True, width=160, color_system=None)
    code = main([str(a) for a in args], console=console)
    return code, console.export_text()


def test_basic_report(sample_log):
    code, output = run([sample_log])
    assert code == 0
    assert "Entries: 7" in output
    assert "Entries by severity" in output
    assert "Connection timeout after <N>ms to <IP>" in output


def test_level_filter(sample_log):
    _, output = run([sample_log, "--level", "warning"])
    assert "Entries: 1" in output
    assert "No recurring errors found." in output


def test_comma_separated_and_repeated_levels(sample_log):
    _, comma = run([sample_log, "-l", "error,info"])
    _, repeated = run([sample_log, "-l", "error", "-l", "info"])
    assert "Entries: 6" in comma
    assert "Entries: 6" in repeated


def test_date_filter(sample_log):
    _, output = run([sample_log, "--since", "2026-11-02", "--until", "2026-11-02"])
    assert "Entries: 2" in output  # only the two ERRORs on Nov 2 (DEBUG is skipped)


def test_exports(sample_log, tmp_path):
    json_path, csv_path = tmp_path / "out.json", tmp_path / "out.csv"
    code, output = run([sample_log, "--json", json_path, "--csv", csv_path])

    assert code == 0
    assert json.loads(json_path.read_text())["total_entries"] == 7
    assert csv_path.read_text().startswith("signature,count")
    assert "Saved JSON:" in output and "Saved CSV:" in output


def test_top_limits_rows(sample_log):
    _, output = run([sample_log, "--min-count", "1", "--top", "1"])
    assert "Top recurring errors (1 of 2)" in output


@pytest.mark.parametrize(
    "args, message",
    [
        (["missing.log"], "file not found"),
        (["{log}", "--level", "verbose"], "Unknown severity"),
        (["{log}", "--since", "soon"], "Invalid date"),
        (["{log}", "--since", "2026-11-05", "--until", "2026-11-01"], "--since must be earlier"),
    ],
)
def test_invalid_input_exits_with_error(sample_log, capsys, args, message):
    args = [a.replace("{log}", str(sample_log)) for a in args]
    with pytest.raises(SystemExit) as exc:
        main(args)
    assert exc.value.code == 2
    assert message in capsys.readouterr().err


def test_bundled_samples_analyse_cleanly():
    _, output = run([SAMPLES_DIR / "app.log", SAMPLES_DIR / "app-node2.log"])
    assert "Top recurring errors" in output


def test_python_dash_m_entry_point(sample_log):
    completed = subprocess.run(
        [sys.executable, "-m", "log_analyzer", str(sample_log), "--level", "error"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert "Entries: 4" in completed.stdout
