# ATK Python SDK

High-level Python wrappers for [ATK (Aerospace Tool Kit)](https://www.osredm.com/atknudt/atk/about).

This is a **third-party** ATK Python SDK that complements and extends the official ATK Python client. It provides:

- Builder pattern for fluent API
- Complete exception hierarchy
- Orbital mechanics utilities
- Dual-mode architecture (Connect + Component)
- Facility and sensor modeling
- Coverage analysis and Walker constellation generation
- Report parsing with pandas DataFrame export

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

    # Create a ground facility with sensor
    facility = atk.create_facility('Beijing', lat=39.9, lon=116.4, height=50)
    sensor = facility.create_sensor('Sensor1', el_start=5, el_end=85,
                                    az_start=0, az_end=360, max_range=2000)

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

    sat_obj = session.create_satellite('Sat1')
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
│   │   ├── exceptions.py       # Exception hierarchy (ATKError root)
│   │   ├── utils.py            # Time parsing, path ops, CMDRESULT parsing
│   │   ├── connect/            # Connect mode
│   │   │   ├── session.py      # ATKConnection + ATKConnectionManager + connect()
│   │   │   ├── session.pyi     # Type stubs (monkey-patched methods)
│   │   │   ├── scenario.py     # ScenarioBuilder
│   │   │   ├── satellite.py    # SatelliteBuilder
│   │   │   ├── facility.py     # FacilityBuilder + SensorBuilder
│   │   │   ├── mcs.py          # McsBuilder
│   │   │   ├── reports.py      # ReportResult + QuickReport + ReportRM
│   │   │   ├── coverage.py     # CoverageBuilder + CoverageStats
│   │   │   └── constellation.py # WalkerBuilder + run_all()
│   │   └── component/          # Component mode
│   │       ├── session.py      # ComponentSession + component_session()
│   │       ├── scenario.py     # ScenarioBuilder (IScenario wrapper)
│   │       ├── satellite.py    # SatelliteBuilder (ISatellite wrapper)
│   │       ├── mcs.py          # McsBuilder (IVADriverMCS wrapper)
│   │       └── reports.py      # ReportExporter
│   ├── vendored/              # ATK-provided SWIG bindings (sibling of atk/)
│   │   ├── ATKConnectModule.py  # SWIG Python wrapper
│   │   ├── _ATKConnectModule.pyd  # Windows native DLL
│   │   └── _ATKConnectModule.so  # Linux native DLL
│   └── tests/                  # Test suite
│       ├── test_utils.py
│       └── connect/
│           ├── test_session.py
│           ├── test_scenario.py
│           ├── test_satellite.py
│           ├── test_mcs.py
│           └── test_facility.py
│
├── examples/
│   ├── connect/
│   │   ├── hohmann_transfer.py
│   │   ├── constellation_coverage.py
│   │   └── create_scenario.py
│   └── component/
│       └── hohmann_transfer.py
│
├── docs/                       # MkDocs documentation (Chinese)
├── README.md
├── PLAN.md
└── pyproject.toml
```

## Documentation

详细文档请参考 [docs/](docs/index.md) 目录：

- [快速开始](docs/guides/getting-started.md) — 5 分钟上手
- [Connect 模式](docs/architecture/connect-mode.md) — TCP 连接和命令发送
- [Component 模式](docs/architecture/component-mode.md) — DLL 直接加载
- [轨道力学基础](docs/guides/orbital-mechanics-primer.md) — 理解示例代码中的公式
- [ATK Connect 命令参考](docs/reference/atk-commands.md) — Connect 命令详细参考

构建文档：

```bash
pip install -e ".[docs]"
mkdocs serve
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

Parameters: `host` (default `"127.0.0.1"`), `port` (default `6655`), `timeout`, `retries`, `backoff`.

#### `ScenarioBuilder` — Scenario management

```python
scenario = atk.create_scenario('Name')
scenario.set_analysis_period('5 Nov 2022', '8 Nov 2022')
scenario.set_analysis_mode('Keplerian')
scenario.save()
scenario.load('path/to/scenario.xml')
scenario.unload()
scenario.animate(forward=True)
scenario.stop_animation()
scenario.open_2d_window()
scenario.open_3d_window()
```

#### `SatelliteBuilder` — Satellite configuration

```python
sat = atk.create_satellite('Sat1', propagator='PropagatorAstromaster')
sat.set_keplerian(sma=7100, ecc=0.001, inc=30, raan=0, argp=0, ta=0)
sat.set_cartesian(x=6678, y=0, z=0, vx=0, vy=7.73, vz=0)
sat.set_state_tle(line1='1 25544U ...', line2='2 25544 ...')
sat.set_mass(500)
sat.set_stage_mass(dry_mass=400, wet_mass=500)
sat.set_attitude('J2000', q1=0, q2=0, q3=0, q4=1)
sat.set_color(12)
sat.run_mcs()
```

#### `FacilityBuilder` — Ground facility

```python
facility = atk.create_facility('Beijing', lat=39.9, lon=116.4, height=50)
facility.set_position(39.9, 116.4, 50)
facility.set_color(5)
```

#### `SensorBuilder` — Sensor configuration

```python
sensor = facility.create_sensor('Sensor1', el_start=5, el_end=85,
                                az_start=0, az_end=360, max_range=2000)
# Or create and configure step by step:
sensor = SensorBuilder(conn, 'Sensor1', facility_name='Beijing')
sensor.create()
sensor.define_conical(el_start=5, el_end=85, az_start=0, az_end=360)
sensor.point_fixed_euler(sequence=123, a1=180, a2=0, a3=0)
sensor.set_range_constraint(max_range_km=2000)
```

#### `McsBuilder` — MCS segment builder

```python
mcs = atk.mcs_builder('*/Satellite/Sat1')
mcs.initial_state_keplerian(sma=6678, ecc=0, inc=28.5, raan=0, argp=0, ta=0)
mcs.initial_state_cartesian(x=6678, y=0, z=0, vx=0, vy=7.73, vz=0)
mcs.propagate_until('10 Jan 2024 12:00:00.000')
mcs.propagate_duration(duration_seconds=5444.0)
mcs.impulsive_burn(dv=[0.5, 0, 0])
mcs.target_sequence(endpoint_path='*/Satellite/Sat2', tolerance=1e-6)
mcs.run()
mcs.apply_changes()
mcs.reset_profiles()
```

#### `ReportResult` — Report parsing

```python
result = atk.quick_report('*/Satellite/Sat1', 'Position', time_period='*')
result.to_dict()        # list[dict[str, str]]
result.to_dataframe()   # pandas DataFrame (requires pandas)
result.data             # raw list[str]
result.columns          # column names
```

```python
result = atk.report_rm('*/Satellite/Sat1', style='J2000PositionVelocity',
                       time_period='1 Jan 2024 7 Jan 2024')
```

#### `CoverageBuilder` — Coverage analysis

```python
cov = atk.create_coverage('GroundCov')
cov.add_asset('*/Satellite/Sat1')
cov.add_facility('*/Facility/Station1')
cov.set_grid_resolution(lat_step=1.0, lon_step=1.0)
stats = cov.compute_stats()
# stats.access_count, stats.total_access_time, stats.mean_access_duration
```

#### `WalkerBuilder` — Walker constellation

```python
walker = atk.constellation_builder('Starlink')
walker.walker_delta(num_satellites=60, num_planes=6, inc=53, alt=550)
walker.set_propagator('PropagatorSGP4')
walker.build()
walker.run_all()  # returns dict[str, bool]
```

### Component Mode

#### `component_session()` — Context manager

```python
with component_session() as session:
    scenario = session.new_scenario('MyScenario')
    sat = session.create_satellite('Sat1')
```

#### `SatelliteBuilder` (Component)

```python
sat = SatelliteBuilder(sat_obj)
sat.set_propagator_type('PropagatorAstromaster')
sat.set_keplerian(sma=6678, ecc=0, inc=28.5, raan=0, argp=0, ta=0)
sat.set_cartesian(x=6678, y=0, z=0, vx=0, vy=7.73, vz=0)
sat.set_mass(500)
sat.set_stage_mass(dry_mass=400, wet_mass=500)
sat.set_attitude_type('J2000')
sat.set_color(12)
driver = sat.get_mcs_driver()
```

#### `McsBuilder` (Component)

```python
mcs = McsBuilder(driver)
mcs.initial_state_keplerian(sma=6678, ecc=0, inc=28.5, raan=0, argp=0, ta=0)
mcs.initial_state_cartesian(x=6678, y=0, z=0, vx=0, vy=7.73, vz=0)
mcs.propagate_until('10 Jan 2024 12:00:00')
mcs.impulsive_burn(dv=[0.5, 0, 0])
mcs.target_sequence(endpoint_path='Satellite/Sat2')
mcs.run()
mcs.apply_changes()
mcs.reset_profiles()
```

#### `ReportExporter` (Component)

```python
from atk.component.reports import ReportExporter

report = ReportExporter(session, sat_obj, 'J2000 Position Velocity',
                        '1 Jan 2024', '7 Jan 2024')
path = report.to_file('output.csv')
```
