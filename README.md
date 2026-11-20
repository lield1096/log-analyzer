# Log Analyzer

[![CI](https://github.com/lield1096/log-analyzer/actions/workflows/ci.yml/badge.svg)](https://github.com/lield1096/log-analyzer/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A lightweight command-line tool that reads application log files, counts
`ERROR` / `WARNING` / `INFO` entries, groups recurring errors, and prints a
clean summary in your terminal. Results can be exported to JSON or CSV.

```
╭───────────────────── Log Analyzer ─────────────────────╮
│ Files: samples/app.log, samples/app-node2.log          │
│ Entries: 850   (skipped 30 unrecognised lines)         │
│ Time range: 2026-11-01 08:11:24 to 2026-11-04 13:50:18 │
╰────────────────────────────────────────────────────────╯
Entries by severity
┏━━━━━━━━━━┳━━━━━━━┳━━━━━━━┓
┃ Severity ┃ Count ┃ Share ┃
┡━━━━━━━━━━╇━━━━━━━╇━━━━━━━┩
│ ERROR    │   112 │ 13.2% │
│ WARNING  │   161 │ 18.9% │
│ INFO     │   577 │ 67.9% │
└──────────┴───────┴───────┘
Top recurring errors (5 of 5)
┏━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
┃ # ┃ Count ┃ Error pattern                                              ┃ Source   ┃ First seen  ┃ Last seen   ┃
┡━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
│ 1 │    49 │ Connection timeout after <N>ms to <IP>                     │ db       │ 11-01 08:22 │ 11-04 12:29 │
│ 2 │    30 │ Payment <N> failed: card declined (request <UUID>)         │ payments │ 11-01 12:28 │ 11-04 13:35 │
│ 3 │    18 │ Unhandled exception in GET /api/orders/<N>: KeyError <STR> │ api      │ 11-01 08:11 │ 11-04 07:08 │
│ 4 │     9 │ Job <N> failed: out of memory                              │ worker   │ 11-01 09:46 │ 11-04 00:43 │
│ 5 │     6 │ SMTP server rejected message to <EMAIL>                    │ email    │ 11-02 11:30 │ 11-03 22:16 │
└───┴───────┴────────────────────────────────────────────────────────────┴──────────┴─────────────┴─────────────┘
```

## Features

* **Parses common log formats** – `2026-11-03 14:22:07 ERROR \[db] message`, with
optional milliseconds, `T` separators, bracketed levels and source tags.
* **Severity counts** – `ERROR`, `WARNING` and `INFO` (aliases such as `WARN`,
`CRITICAL` and `FATAL` are mapped automatically).
* **Recurring error detection** – messages that differ only by numbers, IDs,
IPs, emails or quoted values are grouped into one pattern.
* **Filtering** – by severity and by date/time range.
* **Exports** – full analysis to JSON, recurring errors to CSV.
* **Tiny footprint** – one runtime dependency ([Rich](https://github.com/Textualize/rich)).

## Installation

Requires Python 3.9+.

```bash
git clone https://github.com/lield1096/log-analyzer.git
cd log-analyzer
pip install .
```

For development (adds pytest and ruff):

```bash
pip install -e ".\[dev]"
```

## Usage

```bash
log-analyzer FILE \[FILE ...] \[options]
```

You can also run it as a module: `python -m log\_analyzer FILE ...`.

|Option|Description|
|-|-|
|`-l, --level LEVEL`|Only include these severities. Repeat (`-l error -l warning`) or comma-separate (`-l error,warning`).|
|`--since DATE`|Only entries at or after `DATE` (`YYYY-MM-DD`, `YYYY-MM-DD HH:MM` or `YYYY-MM-DD HH:MM:SS`).|
|`--until DATE`|Only entries at or before `DATE`. A bare date includes the whole day.|
|`--top N`|Number of recurring errors to show (default `10`).|
|`--min-count N`|Occurrences needed for an error to count as recurring (default `2`).|
|`--json PATH`|Export the full analysis to JSON.|
|`--csv PATH`|Export recurring errors to CSV.|
|`--version`|Show the version and exit.|

### Examples

Try these against the bundled synthetic logs in [`samples/`](samples/):

```bash
# Summarise one or more files
log-analyzer samples/app.log samples/app-node2.log

# Only errors and warnings
log-analyzer samples/app.log --level error,warning

# Everything logged on 3 November
log-analyzer samples/app.log --since 2026-11-03 --until 2026-11-03

# Errors in a specific time window
log-analyzer samples/\*.log -l error --since "2026-11-02 08:00" --until "2026-11-02 18:00"

# Show the top 3 patterns, including errors seen only once
log-analyzer samples/app.log --top 3 --min-count 1

# Export results
log-analyzer samples/\*.log --json report.json --csv recurring\_errors.csv
```

### Supported log format

Each entry is one line made of a timestamp, a severity, an optional
`\[source]` tag and the message:

```
2026-11-01 08:00:00 INFO \[auth] User alice logged in
2026-11-01 08:00:00,123 \[WARN] Disk usage at 91%
2026-11-01T08:00:00.123Z ERROR \[db] Connection lost
```

Lines that don't match — stack traces, blank lines, `DEBUG` output — are
skipped and reported as "unrecognised lines" in the summary.

### How recurring errors are grouped

Each `ERROR` message is normalised by replacing variable parts with
placeholders, and messages with the same result are grouped:

|Original|Pattern|
|-|-|
|`Timeout after 3000ms to 10.0.2.9:5432`|`Timeout after <N>ms to <IP>`|
|`Payment 4185 failed (request 016b6287-…)`|`Payment <N> failed (request <UUID>)`|
|`KeyError 'customer\_id'`|`KeyError <STR>`|
|`Mail to bob@example.com bounced`|`Mail to <EMAIL> bounced`|

Hex values (`0xDEADBEEF`) become `<HEX>`.

### Export formats

**JSON** (`--json`) contains the whole analysis:

```json
{
  "files": \["samples/app.log"],
  "total\_entries": 600,
  "skipped\_lines": 21,
  "time\_range": { "start": "2026-11-01 08:11:24", "end": "2026-11-04 13:50:18" },
  "counts": { "ERROR": 77, "WARNING": 112, "INFO": 411 },
  "recurring\_errors": \[
    {
      "signature": "Connection timeout after <N>ms to <IP>",
      "count": 38,
      "first\_seen": "2026-11-01 08:22:10",
      "last\_seen": "2026-11-04 12:29:03",
      "sources": \["db"],
      "example": "Connection timeout after 3000ms to 10.0.2.209:5432"
    }
  ]
}
```

**CSV** (`--csv`) has one row per recurring error, with the columns
`signature, count, first\_seen, last\_seen, sources, example`. Multiple sources
are joined with `;`.

Filters apply to both the terminal report and the exports.

## Project structure

```
log-analyzer/
├── src/log\_analyzer/
│   ├── cli.py         # argument parsing and orchestration
│   ├── parser.py      # log lines -> LogEntry objects
│   ├── filters.py     # severity and date filtering
│   ├── analyzer.py    # counts and recurring-error grouping
│   ├── report.py      # Rich terminal output
│   ├── exporters.py   # JSON and CSV export
│   └── models.py      # Severity and LogEntry
├── tests/             # pytest suite
├── samples/           # synthetic demo logs
├── scripts/generate\_samples.py
└── .github/workflows/ci.yml
```

Data flows in one direction: **parse → filter → analyze → report / export**.
Each step is a plain function, so they're easy to reuse from Python:

```python
from log\_analyzer.analyzer import analyze
from log\_analyzer.filters import filter\_entries
from log\_analyzer.models import Severity
from log\_analyzer.parser import parse\_files

parsed = parse\_files(\["samples/app.log"])
errors = filter\_entries(parsed.entries, severities=\[Severity.ERROR])
for group in analyze(errors).recurring\_errors:
    print(group.count, group.signature)
```

## Development

```bash
pip install -e ".\[dev]"
pytest              # run the tests
ruff check .        # lint
ruff format .       # format
python scripts/generate\_samples.py   # regenerate the demo logs
```

CI runs lint and the test suite on Python 3.9 – 3.13 for every push and pull request.

## Contributing

Contributions are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE)

