# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Test Commands

```bash
pip install -e ".[dev]"              # install with dev dependencies
python -m pytest src/tests/ -v       # run all tests
python -m pytest src/tests/test_utils.py -v                          # single file
python -m pytest src/tests/test_utils.py::TestParseAtkTime::test_full_datetime -v  # single test
python -m pytest src/tests/ -v --cov=src --cov-report=term-missing  # with coverage
pip install -e ".[docs]" && mkdocs serve  # build docs locally
```

No linter or formatter is configured. No CI pipeline exists.

## Architecture

ATK Python SDK wraps ATK (Aerospace Tool Kit) via two independent modes:

- **Connect mode** (`atk.connect`) — TCP to a running ATK GUI. Uses vendored SWIG bindings (`src/vendored/ATKConnectModule`). Entry: `connect()` context manager → `ATKConnection`.
- **Component mode** (`atk.component`) — Direct DLL load, no GUI needed. Requires ATK installation (`ATK_ROOT` env). Entry: `component_session()` context manager → `ComponentSession`.

Both modes share `atk.exceptions` (hierarchy rooted at `ATKError`) and `atk.utils` (time parsing, path ops, `CMDRESULT` parsing).

### Connect mode monkey-patching

Each connect submodule (scenario, satellite, mcs, reports, coverage, constellation) calls `_patch_connection()` at import time to inject factory methods onto `ATKConnection`. This is triggered by `connect/__init__.py` importing all submodules. Do not remove those imports.

### Vendored native libraries

`src/vendored/` contains SWIG-generated Python wrappers and platform-specific native extensions (`.pyd` for Windows, `.so` for Linux). These are ATK-provided binaries — do not modify them. The `__init__.py` re-exports SWIG functions for the SDK to import.

### Builder pattern

Both modes use fluent builders (`ScenarioBuilder`, `SatelliteBuilder`, `McsBuilder`). Connect mode builders wrap command strings sent over TCP. Component mode builders wrap SWIG object references (`IScenario`, `ISatellite`, `IVADriverMCS`).

## Key Conventions

- **src layout**: package code lives in `src/atk/`, tests in `src/tests/`
- **No runtime dependencies**: the SDK has zero pip dependencies
- **Unit tests mock SWIG**: all tests use `unittest.mock.MagicMock` to mock native bindings — no ATK installation needed to run tests
- **Component mode tests are missing**: `src/tests/component/` has no test files yet
- **Documentation is in Chinese**: `docs/` and `PLAN.md` are Chinese-language
