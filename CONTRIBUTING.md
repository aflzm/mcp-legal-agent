# Contributing to MCP Legal Agent

Thanks for your interest in improving this project! This document explains how
to set up a development environment, run the tests, and submit changes.

## Development setup

Requires **Python 3.10+** (3.12 recommended).

```bash
python -m venv .venv
# Windows
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
# POSIX
.venv/bin/python -m pip install -r requirements-dev.txt
```

The project is fully offline by default (`MOCK_MODE=true`); no API key or
network access is needed to run the demo or the test suite.

## Running the checks

```bash
python -m unittest discover -s tests -v   # functional tests
ruff check .                              # lint
python demo.py                            # offline smoke test
```

Please make sure all of these pass before opening a pull request.

## Project conventions

- Keep the tool **stateless**: it must not hold session state between calls.
- Preserve the control guarantees — search budget accounting, monotonic
  evidence grading, and per-request isolation — when changing the harness.
- Never present Mock fallbacks as real model output. Any degraded path must be
  labeled with its `mock:*` backend tag.
- Match the existing style: type-annotated functions, `from __future__ import
  annotations`, and the configured Ruff rules (`E`, `F`, `I`).

## Pull requests

1. Fork the repository and create a topic branch.
2. Make focused changes with a clear rationale.
3. Add or update tests where behavior changes.
4. Run the checks above.
5. Open a pull request using the provided template.

## Reporting issues

Use the [issue templates](.github/ISSUE_TEMPLATE) for bug reports and feature
requests. For a bug report, please include reproduction steps, expected vs.
actual behavior, your Python version, and any relevant trace output.

## Code of Conduct

By participating, you agree to abide by the [Code of Conduct](CODE_OF_CONDUCT.md).