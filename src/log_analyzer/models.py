"""Core data structures shared across the package."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class Severity(str, Enum):
    """Supported log severities, ordered from most to least severe."""

    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"

    @classmethod
    def from_string(cls, value: str) -> Severity:
        """Parse a severity name, accepting common aliases (WARN, FATAL, ...)."""
        normalized = value.strip().upper()
        aliases = {
            "WARN": cls.WARNING,
            "CRITICAL": cls.ERROR,
            "FATAL": cls.ERROR,
        }
        if normalized in aliases:
            return aliases[normalized]
        try:
            return cls(normalized)
        except ValueError:
            valid = ", ".join(s.value for s in cls)
            raise ValueError(f"Unknown severity '{value}'. Expected one of: {valid}") from None


@dataclass(frozen=True)
class LogEntry:
    """A single parsed log line."""

    timestamp: datetime
    severity: Severity
    message: str
    source: str | None = None
    file: str = ""
    line_number: int = 0

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(sep=" "),
            "severity": self.severity.value,
            "source": self.source,
            "message": self.message,
            "file": self.file,
            "line_number": self.line_number,
        }
