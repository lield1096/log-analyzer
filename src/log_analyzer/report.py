"""Render an :class:`AnalysisResult` in the terminal with Rich."""

from __future__ import annotations

from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table

from .analyzer import AnalysisResult
from .models import Severity

SEVERITY_STYLES = {
    Severity.ERROR: "bold red",
    Severity.WARNING: "yellow",
    Severity.INFO: "cyan",
}


def _format_range(result: AnalysisResult) -> str:
    if result.start is None or result.end is None:
        return "-"
    return f"{result.start:%Y-%m-%d %H:%M:%S} to {result.end:%Y-%m-%d %H:%M:%S}"


def render_report(result: AnalysisResult, console: Console | None = None, top: int = 10) -> None:
    """Print the summary panel, severity table and recurring-errors table."""
    console = console or Console()

    overview = (
        f"[bold]Files:[/bold] {escape(', '.join(result.files)) or '-'}\n"
        f"[bold]Entries:[/bold] {result.total_entries}"
        f"   [dim](skipped {result.skipped_lines} unrecognised lines)[/dim]\n"
        f"[bold]Time range:[/bold] {_format_range(result)}"
    )
    console.print(Panel(overview, title="Log Analyzer", border_style="blue", expand=False))

    severity_table = Table(title="Entries by severity", title_justify="left")
    severity_table.add_column("Severity")
    severity_table.add_column("Count", justify="right")
    severity_table.add_column("Share", justify="right")
    for severity in Severity:
        count = result.counts.get(severity, 0)
        share = f"{count / result.total_entries:.1%}" if result.total_entries else "-"
        style = SEVERITY_STYLES[severity]
        severity_table.add_row(f"[{style}]{severity.value}[/{style}]", str(count), share)
    console.print(severity_table)

    if not result.recurring_errors:
        console.print("[green]No recurring errors found.[/green]")
        return

    shown = result.recurring_errors[:top]
    errors_table = Table(
        title=f"Top recurring errors ({len(shown)} of {len(result.recurring_errors)})",
        title_justify="left",
    )
    errors_table.add_column("#", justify="right", style="dim")
    errors_table.add_column("Count", justify="right", style="bold red")
    errors_table.add_column("Error pattern", overflow="fold")
    errors_table.add_column("Source")
    errors_table.add_column("First seen")
    errors_table.add_column("Last seen")
    for index, group in enumerate(shown, start=1):
        errors_table.add_row(
            str(index),
            str(group.count),
            escape(group.signature),
            escape(", ".join(group.sources)) or "-",
            f"{group.first_seen:%m-%d %H:%M}",
            f"{group.last_seen:%m-%d %H:%M}",
        )
    console.print(errors_table)
