# Connect 模式架构

## 概述

Connect 模式通过 TCP 网络连接向运行中的 ATK 软件发送 Connect 命令字符串，实现对 ATK 内部对象的操作。这种模式需要 ATK 软件在后台运行并监听连接端口。

```
用户代码
    │
    └── ATK Python SDK（本库） ──────► ATK 软件（运行中）
              │                              │
              │  connect()                    │
              │  create_satellite()          │
              │  create_facility()           │
              │  mcs_builder()               │
              │  quick_report()              │
              │                              TCP 127.0.0.1:6655
```

## SDK 核心接口

本库提供简洁的上下文管理器接口：

### connect() — 连接管理

```python
from atk.connect import connect

with connect() as atk:
    # atk 是 ATKConnection 对象
    pass

# 自定义连接参数
with connect(host='192.168.1.10', port=6655, retries=5, backoff=3.0) as atk:
    pass
```

**参数**：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `host` | `"127.0.0.1"` | ATK 服务器地址 |
| `port` | `6655` | ATK 监听端口 |
| `timeout` | `30.0` | 连接超时（秒） |
| `retries` | `3` | 重试次数 |
| `backoff` | `2.0` | 重试间隔（秒） |

### ATKConnection 主要方法

| 方法 | 说明 |
|------|------|
| `create_scenario(name)` | 创建场景，返回 `ScenarioBuilder` |
| `create_satellite(name)` | 创建卫星，返回 `SatelliteBuilder` |
| `create_facility(name, lat, lon, height)` | 创建地面站，返回 `FacilityBuilder` |
| `create_coverage(name)` | 创建覆盖分析，返回 `CoverageBuilder` |
| `constellation_builder(name)` | 创建星座构建器，返回 `WalkerBuilder` |
| `mcs_builder(satellite_path)` | 创建 MCS 构建器，返回 `McsBuilder` |
| `quick_report(obj_path, style, time_period)` | 执行快速报告，返回 `ReportResult` |
| `report_rm(obj_path, style, time_period)` | 执行 Report_RM 报告，返回 `ReportResult` |
| `send(command, obj_path, param)` | 发送原生 Connect 命令 |
| `send_str(command, obj_path, param)` | 发送命令并返回字符串响应 |

### ATKConnectionManager — 带重试的连接管理

```python
from atk.connect.session import ATKConnectionManager

mgr = ATKConnectionManager('127.0.0.1', 6655, retries=5, backoff=3.0)
conn = mgr.connect()
# ...
conn.close()
```

### 使用示例

```python
from atk.connect import connect

with connect() as atk:
    # 创建场景
    scenario = atk.create_scenario('MyScenario')
    scenario.set_analysis_period('1 Jan 2024', '7 Jan 2024')

    # 创建卫星
    sat = atk.create_satellite('Sat1')
    sat.set_propagator('PropagatorAstromaster')
    sat.set_keplerian(sma=7100, ecc=0.001, inc=30, raan=0, argp=0, ta=0)
    sat.run_mcs()

    # 创建地面站和传感器
    facility = atk.create_facility('Beijing', lat=39.9, lon=116.4, height=50)
    sensor = facility.create_sensor('Sensor1', el_start=5, el_end=85,
                                    az_start=0, az_end=360, max_range=2000)

    # 查询报告
    result = atk.quick_report('*/Satellite/Sat1', 'Position', time_period='*')
    df = result.to_dataframe()

    # 保存场景
    scenario.save()
```

详见 [快速开始](../guides/getting-started.md)。

## 构建器模式

### ScenarioBuilder — 场景管理

```python
scenario = atk.create_scenario('MyMission')
scenario.set_analysis_period('1 Jan 2024', '7 Jan 2024')
scenario.set_analysis_mode('Keplerian')   # Keplerian / Spice / Fixed
scenario.animate(forward=True)
scenario.stop_animation()
scenario.open_2d_window()
scenario.open_3d_window()
scenario.save()
scenario.save(path='C:/path/to/scenario.xml')
scenario.load('C:/path/to/scenario.xml')
scenario.unload()
scenario.quick_report('*/Satellite/Sat1', 'Position', time_period='*')
```

### SatelliteBuilder — 卫星配置

```python
sat = atk.create_satellite('Sat1')
sat.set_propagator('PropagatorAstromaster')
sat.set_keplerian(sma=7100, ecc=0.001, inc=30, raan=0, argp=0, ta=0)
sat.set_cartesian(x=6678, y=0, z=0, vx=0, vy=7.73, vz=0)
sat.set_state_tle(line1='1 25544U ...', line2='2 25544 ...')
sat.set_mass(500)
sat.set_stage_mass(dry_mass=400, wet_mass=500)
sat.set_attitude('J2000', q1=0, q2=0, q3=0, q4=1)
sat.set_color(12)
sat.run_mcs()
```

**传播器**：`PropagatorTwoBody`、`PropagatorJ2Perturbation`、`PropagatorHPOP`、
`PropagatorSGP4`（通过 TLE）、`PropagatorAstromaster`、`PropagatorJ4Perturbation` 等。

### FacilityBuilder — 地面站

```python
facility = atk.create_facility('Beijing', lat=39.9, lon=116.4, height=50)
facility.set_position(39.9, 116.4, 50)  # Geodetic 坐标
facility.set_color(5)

# 在地面站下创建传感器
sensor = facility.create_sensor('Sensor1', el_start=5, el_end=85,
                                az_start=0, az_end=360, max_range=2000)
```

### SensorBuilder — 传感器配置

通常通过 `FacilityBuilder.create_sensor()` 创建，也可直接实例化：

```python
sensor = SensorBuilder(conn, 'Sensor1', facility_name='Beijing')
sensor.create()
sensor.define_conical(el_start=5, el_end=85, az_start=0, az_end=360)
sensor.point_fixed_euler(sequence=123, a1=180, a2=0, a3=0)
sensor.set_range_constraint(max_range_km=2000)
```

### McsBuilder — MCS 段构建

```python
mcs = atk.mcs_builder('*/Satellite/Sat1')
mcs.initial_state_keplerian(sma=6678, ecc=0, inc=28.5, raan=0, argp=0, ta=0)
mcs.initial_state_cartesian(x=6678, y=0, z=0, vx=0, vy=7.73, vz=0)
mcs.propagate_until('10 Jan 2024 12:00:00.000')
mcs.propagate_duration(duration_seconds=5444.0)
mcs.impulsive_burn(dv=[0.5, 0, 0])
mcs.target_sequence(endpoint_path='*/Satellite/Sat2')
mcs.run()
mcs.apply_changes()
mcs.reset_profiles()
```

### 报告系统

```python
# QuickReport — 快速报告
result = atk.quick_report('*/Satellite/Sat1', 'Position', time_period='*')
result.data           # list[str] — 原始数据行
result.columns        # list[str] — 列标题
result.to_dict()      # list[dict[str, str]]
result.to_dataframe() # pandas DataFrame

# ReportRM — 带文件输出的报告
result = atk.report_rm('*/Satellite/Sat1', style='J2000PositionVelocity',
                       time_period='1 Jan 2024 7 Jan 2024')
```

**已知报告样式及列名**：

| 样式 | 列 |
|------|-----|
| `Position` | time, x, y, z, vx, vy, vz |
| `Keplerian` | time, sma, ecc, inc, raan, argp, ta |
| `J2000Position` | time, x, y, z |
| `J2000PositionVelocity` | time, x, y, z, vx, vy, vz |
| `LLA` | time, lat, lon, alt |
| `Access` | time, access |
| `AER` | time, az, el, range |

## 底层依赖

Connect 模式底层依赖 ATK 官方的 `ATKConnectModule`，提供三个原生函数：

| 函数 | 说明 |
|------|------|
| `atkOpen(host, port)` | 建立 TCP 连接 |
| `atkConnect(conID, cmd, inputStr)` | 发送 Connect 命令 |
| `atkClose(conID)` | 关闭连接 |

### atkConnect 返回值

`atkConnect()` 可能返回两种类型：

1. **`str`** — 简单响应（如 `"ACK"`、`"NACK"`）
2. **`CMDRESULT`** — 复杂响应（包含 `m_vectData` 属性）

SDK 的 `send()` 方法内部统一处理这两种情况，自动检测错误并抛出 `ATKCommandError`。

如需深入了解 Connect 命令格式和协议，参考 ATK 官方文档：
**https://gitcode.com/jinke18/atk-doc** — `二次开发教程/2-二次开发CONNECT模式/`
