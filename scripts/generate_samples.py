"""Regenerate the synthetic demo logs in ``samples/``.

The output is deterministic (fixed random seed), so re-running this script
produces identical files. Run from the repository root::

    python scripts/generate_samples.py
"""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path

SAMPLES = Path(__file__).resolve().parent.parent / "samples"

INFO = [
    ("auth", "User {user} logged in"),
    ("auth", "User {user} logged out"),
    ("api", "GET /api/orders/{n} 200 in {ms}ms"),
    ("api", "POST /api/cart 201 in {ms}ms"),
    ("worker", "Job {n} completed in {ms}ms"),
    ("cache", "Cache refreshed ({n} keys)"),
]
WARNINGS = [
    ("api", "Slow response: GET /api/search took {slow}ms"),
    ("db", "Connection pool at {pct}% capacity"),
    ("auth", "Failed login attempt for user {user} from {ip}"),
    ("worker", "Retrying job {n} (attempt {attempt}/3)"),
]
ERRORS = [  # (weight, source, template)
    (8, "db", "Connection timeout after {ms}ms to {ip}:5432"),
    (5, "payments", "Payment {n} failed: card declined (request {uuid})"),
    (4, "api", "Unhandled exception in GET /api/orders/{n}: KeyError 'customer_id'"),
    (2, "worker", "Job {n} failed: out of memory"),
    (1, "email", "SMTP server rejected message to {user}@example.com"),
]


def fill(template: str, rng: random.Random) -> str:
    return template.format(
        user=rng.choice(["alice", "bob", "carol", "dave", "erin"]),
        n=rng.randint(1000, 9999),
        ms=rng.randint(20, 900) if "timeout" not in template else rng.choice([3000, 5000]),
        slow=rng.randint(2000, 8000),
        pct=rng.randint(80, 98),
        ip=f"10.0.{rng.randint(0, 3)}.{rng.randint(2, 254)}",
        attempt=rng.randint(1, 3),
        uuid=uuid.UUID(int=rng.getrandbits(128)),
    )


def generate(path: Path, start: datetime, lines: int, seed: int) -> None:
    rng = random.Random(seed)
    now = start
    out = []
    for _ in range(lines):
        now += timedelta(seconds=rng.randint(30, 900))
        roll = rng.random()
        if roll < 0.12:
            weights = [w for w, _, _ in ERRORS]
            _, source, template = rng.choices(ERRORS, weights=weights)[0]
            level = "ERROR"
        elif roll < 0.30:
            source, template = rng.choice(WARNINGS)
            level = "WARNING"
        else:
            source, template = rng.choice(INFO)
            level = "INFO"
        out.append(f"{now:%Y-%m-%d %H:%M:%S} {level} [{source}] {fill(template, rng)}")
        # Occasionally include a stack trace, which the parser should skip.
        if level == "ERROR" and rng.random() < 0.15:
            out.append("Traceback (most recent call last):")
            out.append('  File "app/handlers.py", line 42, in handle')
            out.append("    raise RuntimeError('boom')")
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


if __name__ == "__main__":
    SAMPLES.mkdir(exist_ok=True)
    generate(SAMPLES / "app.log", datetime(2026, 11, 1, 8, 0, 0), lines=600, seed=42)
    generate(SAMPLES / "app-node2.log", datetime(2026, 11, 2, 9, 30, 0), lines=250, seed=7)
    print(f"Wrote sample logs to {SAMPLES}")
