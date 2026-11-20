# Contributing to Log Analyzer

Thanks for your interest in improving Log Analyzer! Bug reports, ideas and
pull requests are all welcome.

## Reporting issues

When opening an issue, please include:

- what you ran (the full command),
- what you expected and what happened instead,
- a few sample log lines that reproduce the problem (remove anything sensitive),
- your Python version and operating system.

## Setting up a development environment

```bash
git clone https://github.com/OWNER/log-analyzer.git
cd log-analyzer
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Before you open a pull request

1. Create a branch from `main`.
2. Keep the change focused — one feature or fix per pull request.
3. Add or update tests in `tests/` for any behaviour you change.
4. Make sure everything passes locally:

   ```bash
   pytest
   ruff check .
   ruff format --check .
   ```

5. Update `README.md` if you add or change a command-line option.

CI runs the same checks on Python 3.9 – 3.13, so a green local run usually
means a green CI run.

## Code guidelines

- **Keep it simple.** The project aims to stay small and easy to read. Prefer
  plain functions and the standard library; please discuss new dependencies in
  an issue first.
- **One job per module.** Parsing lives in `parser.py`, filtering in
  `filters.py`, grouping in `analyzer.py`, terminal output in `report.py`, and
  file output in `exporters.py`. `cli.py` only wires them together.
- **Type hints and docstrings** on public functions.
- **No real log data** in tests or samples. Use synthetic lines; to change the
  demo logs, edit and re-run `scripts/generate_samples.py`.

## Common contributions

- *Supporting a new log format:* extend `LINE_PATTERN` in `parser.py` and add
  examples to `tests/test_parser.py`.
- *Improving error grouping:* add a pattern to `_NORMALIZERS` in
  `analyzer.py` (order matters — specific patterns before the generic number
  rule) and add a case to `test_normalize_message`.

## Code of conduct

Be respectful and constructive. We want this to be a welcoming project for
contributors of all experience levels.
