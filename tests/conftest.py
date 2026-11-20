from pathlib import Path

import pytest

SAMPLE_LOG = """\
2026-11-01 08:00:00 INFO [auth] User alice logged in
2026-11-01 08:05:00 WARNING [db] Connection pool at 85% capacity
2026-11-01 09:00:00 ERROR [db] Connection timeout after 3000ms to 10.0.0.12:5432
Traceback (most recent call last):
  File "app.py", line 1, in <module>
2026-11-02 10:00:00 ERROR [db] Connection timeout after 5000ms to 10.0.1.7:5432
2026-11-02 11:00:00 ERROR [payments] Payment 1234 failed: card declined
2026-11-02 12:00:00 DEBUG [cache] cache warm
2026-11-03 13:00:00 INFO [api] GET /api/orders/99 200 in 15ms
2026-11-03 14:00:00 ERROR [db] Connection timeout after 3000ms to 10.0.0.99:5432
"""


@pytest.fixture
def sample_log(tmp_path: Path) -> Path:
    path = tmp_path / "app.log"
    path.write_text(SAMPLE_LOG, encoding="utf-8")
    return path
