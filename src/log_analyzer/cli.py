"""Command-line interface: ``log-analyzer FILE [FILE ...] [options]``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich.console import Console

from . import __version__
from .analyzer import analyze
from .exporters import export_csv, export_json
from .filters import filter_entries, parse_date
from .models import Severity
from .parser import parse_files
from .report import render_report


def _severity_list(value: str) -> list[Severity]:
    """Accept ``ERROR`` or ``error,warning`` for --level."""
    try:
        return [Severity.from_string(part) for part in value.split(",") if part.strip()]
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="log-analyzer",
        description="Summarise application log files and find recurring errors.",
    )
    parser.add_argument("files", nargs="+", type=Path, help="one or more log files to analyse")
    parser.add_argument(
        "-l",
        "--level",
        type=_severity_list,
        action="append",
        metavar="LEVEL",
        help="only include these severities (ERROR, WARNING, INFO); repeat or comma-separate",
    )
    parser.add_argument(
        "--since", metavar="DATE", help="only entries at or after DATE (YYYY-MM-DD[ HH:MM[:SS]])"
    )
    parser.add_argument(
        "--until", metavar="DATE", help="only entries at or before DATE (a bare date includes the whole day)"
    )
    parser.add_argument(
        "--top", type=int, default=10, metavar="N", help="recurring errors to show (default: 10)"
    )
    parser.add_argument(
        "--min-count",
        type=int,
        default=2,
        metavar="N",
        help="occurrences needed for an error to count as recurring (default: 2)",
    )
    parser.add_argument("--json", type=Path, metavar="PATH", help="export results to a JSON file")
    parser.add_argument("--csv", type=Path, metavar="PATH", help="export recurring errors to a CSV file")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: list[str] | None = None, console: Console | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    console = console or Console()

    missing = [str(path) for path in args.files if not path.is_file()]
    if missing:
        parser.error(f"file not found: {', '.join(missing)}")

    try:
        since = parse_date(args.since) if args.since else None
        until = parse_date(args.until, end_of_day=True) if args.until else None
    except ValueError as exc:
        parser.error(str(exc))
    if since and until and since > until:
        parser.error("--since must be earlier than --until")

    severities = [s for group in args.level for s in group] if args.level else None

    parsed = parse_files(args.files)
    entries = filter_entries(parsed.entries, severities=severities, since=since, until=until)
    result = analyze(
        entries,
        min_count=args.min_count,
        files=parsed.files,
        skipped_lines=parsed.skipped_lines,
    )

    render_report(result, console=console, top=args.top)

    if args.json:
        console.print(f"[green]Saved JSON:[/green] {export_json(result, args.json)}")
    if args.csv:
        console.print(f"[green]Saved CSV:[/green] {export_csv(result, args.csv)}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
