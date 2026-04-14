# ATK Python SDK

High-level Python wrappers for [ATK (Analytical Toolkit)](https://www.analytickit.com))
supporting two operation modes:

| Mode | Requires ATK GUI | How it works |
|------|-----------------|--------------|
| **Connect** | Yes (must be running) | TCP connection → Connect commands |
| **Component** | No | Direct DLL load → OO API |

## Installation

```bash
pip install -e .
```

This installs the `atk` package in editable mode and makes `vendored/` available
for import. After installation:

```python
from atk.connect import connect           # Connect mode
from atk.component import component_session  # Component mode
```

### Vendored ATK Files

The `vendored/` directory contains ATK-provided SWIG bindings:

| File | Purpose |
|------|---------|
| `vendored/ATKConnectModule.py` | Connect mode Python wrapper |
| `vendored/_ATKConnectModule.pyd` | Connect mode Windows DLL |
| `vendored/_ATKConnectModule.so` | Connect mode Linux x64 DLL |

**ATK Component mode** additionally requires `ATKComponentPythonModule.py` and
`_ATKComponentPythonModule.pyd` from the ATK installation. Either:
- Copy them into `vendored/`, OR
- Set `ATK_ROOT=C:\Users\ouyan\ATK\ATK-v4.0-rc.4` (or your ATK install path)

## Quick Start

### Connect Mode

Requires ATK software running on `127.0.0.1:6655`:

```python
from atk.connect import connect

with connect() as atk:
    scenario = atk.create_scenario('MyMission')
    scenario.set_analysis_period('1 Jan 2024', '7 Jan 2024')

    sat = atk.create_satellite('Sat1')
    sat.set_propagator('PropagatorAstromaster')
    sat.set_keplerian(sma=7100, ecc=0.001, inc=30, raan=0, argp=0, ta=0)
    sat.set_mass(500)
    sat.run_mcs()

    # Run a report
    result = atk.quick_report('*/Satellite/Sat1', 'Position', time_period='*')
    df = result.to_dataframe()  # requires pandas
```

### Component Mode

Requires ATK Component files (see above):

```python
from atk.component import component_session
from atk.component.satellite import SatelliteBuilder
from atk.component.mcs import McsBuilder

with component_session() as session:
    scenario = session.new_scenario('MyMission')
    scenario.set_analysis_period('1 Jan 2024', '7 Jan 2024')

    sat_obj = scenario.create_satellite('Sat1')
    sat = SatelliteBuilder(sat_obj)
    sat.set_propagator_type('PropagatorAstromaster')

    driver = sat.get_mcs_driver()
    mcs = McsBuilder(driver)
    mcs.initial_state_keplerian(sma=6678, ecc=0, inc=28.5, raan=0, argp=0, ta=0)
    mcs.propagate_duration(duration_seconds=5444.0)
    mcs.run()
```

## Project Structure

```
atk-python-sdk/
├── src/
│   ├── atk/                    # Python SDK source
│   │   ├── __init__.py
│   │   ├── exceptions.py
│   │   ├── utils.py
│   │   ├── connect/            # Connect mode
│   │   │   ├── session.py       # ATKConnection + connect()
│   │   │   ├── scenario.py      # ScenarioBuilder
│   │   │   ├── satellite.py    # SatelliteBuilder
│   │   │   ├── mcs.py          # McsBuilder
│   │   │   ├── reports.py       # ReportResult + to_dataframe()
│   │   │   ├── coverage.py     # CoverageBuilder
│   │   │   └── constellation.py # WalkerBuilder + run_all()
│   │   └── component/          # Component mode
│   │       ├── session.py       # ComponentSession + component_session()
│   │       ├── scenario.py      # ScenarioBuilder (IScenario wrapper)
│   │       ├── satellite.py    # SatelliteBuilder (ISatellite wrapper)
│   │       ├── mcs.py          # McsBuilder (IVADriverMCS wrapper)
│   │       └── reports.py       # ReportExporter
│   ├── vendored/              # ATK-provided SWIG bindings (sibling of atk/)
│   │   ├── ATKConnectModule.py  # SWIG Python wrapper
│   │   ├── _ATKConnectModule.pyd  # Windows native DLL
│   │   └── _ATKConnectModule.so  # Linux native DLL
│   └── tests/                  # Test suite (51 tests)
│       ├── test_utils.py
│       └── connect/
│           ├── test_session.py
│           ├── test_scenario.py
│           ├── test_satellite.py
│           └── test_mcs.py
│
├── examples/
│   ├── connect/
│   │   ├── hohmann_transfer.py
│   │   └── constellation_coverage.py
│   └── component/
│       └── hohmann_transfer.py
│
├── README.md
├── PLAN.md
└── pyproject.toml
```

## Running Tests

```bash
pip install -e ".[dev]"
python -m pytest src/tests/ -v
```

## API Reference

### Connect Mode

#### `atk.connect.connect(host, port)` — Context manager

```python
with connect('127.0.0.1', 6655) as atk:
    atk.send('New', '*/Scenario/MyScenario', '')
```

#### `ScenarioBuilder` — Scenario creation

```python
scenario = atk.create_scenario('Name')
scenario.set_analysis_period('5 Nov 2022', '8 Nov 2022')
scenario.save()
```

#### `SatelliteBuilder` — Satellite configuration

```python
sat = atk.create_satellite('Sat1', propagator='PropagatorAstromaster')
sat.set_keplerian(sma=7100, ecc=0.001, inc=30, raan=0, argp=0, ta=0)
sat.set_mass(500)
sat.run_mcs()
```

#### `McsBuilder` — MCS segment builder

```python
mcs = atk.mcs_builder('*/Satellite/Sat1')
mcs.initial_state_keplerian(sma=6678, ecc=0, inc=28.5, raan=0, argp=0, ta=0)
mcs.propagate_until('10 Jan 2024 12:00:00.000')
mcs.impulsive_burn(dv=[0.5, 0, 0])
mcs.run()
```

#### `CoverageBuilder` — Coverage analysis

```python
cov = atk.create_coverage('GroundCov')
cov.add_asset('*/Satellite/Sat1')
cov.add_facility('*/Facility/Station1')
stats = cov.compute_stats()
```

#### `WalkerBuilder` — Walker constellation

```python
walker = atk.constellation_builder('Starlink')
walker.walker_delta(num_satellites=60, num_planes=6, inc=53, alt=550)
walker.build()
walker.run_all(max_workers=8)
```

### Component Mode

#### `component_session()` — Context manager

```python
with component_session() as session:
    scenario = session.new_scenario('MyScenario')
    sat = scenario.create_satellite('Sat1')
```

#### `SatelliteBuilder` (Component)

```python
sat = SatelliteBuilder(sat_obj)
sat.set_propagator_type('PropagatorAstromaster')
driver = sat.get_mcs_driver()
mcs = McsBuilder(driver)
mcs.initial_state_keplerian(sma=6678, ecc=0, ...)
mcs.run()
```
