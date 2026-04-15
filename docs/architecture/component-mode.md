# Component 模式架构

## 概述

Component 模式直接加载 ATK 原生 DLL，通过本库封装的高层次 API 操作 ATK 内部对象，无需 ATK 软件运行。

```
用户代码
    │
    └── ATK Python SDK（本库） ──────► ATK DLL
              │                              │
              │  component_session()          │
              │  SatelliteBuilder()           │
              │  McsBuilder()               │
              │  ReportExporter()             │
              ▼                              ▼
         Python 接口                   ATK 原生 DLL
```

## SDK 核心接口

### component_session() — 会话管理

```python
from atk.component import component_session

with component_session() as session:
    # session 是 ComponentSession 对象
    pass
```

### ComponentSession 主要方法

| 方法 | 说明 |
|------|------|
| `new_scenario(name)` | 创建新场景 |
| `load_scenario(path)` | 加载场景文件 |
| `save_scenario(path?)` | 保存场景 |
| `close_scenario()` | 关闭当前场景 |
| `create_satellite(name)` | 创建卫星 |
| `get_object(path)` | 按路径获取对象 |
| `object_exists(path)` | 检查对象是否存在 |
| `play()` | 正向播放动画 |
| `reset()` | 重置动画到开始时间 |
| `output_report(obj, type, start, stop, path?)` | 生成数据报告 |

### ScenarioBuilder — 场景管理

```python
from atk.component.scenario import ScenarioBuilder

# 通过 ComponentSession 创建场景
scenario = session.new_scenario('MyScenario')
# 或使用封装类
builder = ScenarioBuilder(session, scenario)
builder.set_analysis_period('1 Jan 2024', '7 Jan 2024')
builder.set_start_time('1 Jan 2024 00:00:00.000')
builder.set_stop_time('7 Jan 2024 00:00:00.000')
builder.save()
builder.save(path='C:/path/to/scenario.xml')
builder.play()
builder.reset()
builder.create_satellite('Sat1')
builder.get_satellites()  # 返回场景中所有卫星列表
```

### SatelliteBuilder — 卫星配置

```python
from atk.component.satellite import SatelliteBuilder

sat = SatelliteBuilder(sat_obj)
sat.set_propagator_type('PropagatorAstromaster')
sat.set_keplerian(sma=7100, ecc=0.001, inc=30, raan=0, argp=0, ta=0)
sat.set_cartesian(x=6678, y=0, z=0, vx=0, vy=7.73, vz=0)
sat.set_mass(500)
sat.set_stage_mass(dry_mass=400, wet_mass=500)
sat.set_attitude_type('J2000')
sat.set_color(12)
driver = sat.get_mcs_driver()
```

**传播器**：`PropagatorTwoBody`、`PropagatorJ2Perturbation`、`PropagatorHPOP`、
`PropagatorSGP4`、`PropagatorAstromaster`、`PropagatorJ4Perturbation` 等。

### McsBuilder — 机动序列构建

```python
from atk.component.mcs import McsBuilder

# 接受 ISatellite 或 IVADriverMCS
mcs = McsBuilder(sat_obj)  # 或 McsBuilder(driver)
mcs.initial_state_keplerian(sma=6678, ecc=0, inc=28.5, raan=0, argp=0, ta=0)
mcs.initial_state_cartesian(x=6678, y=0, z=0, vx=0, vy=7.73, vz=0)
mcs.propagate_until('10 Jan 2024 12:00:00')
mcs.propagate_duration(duration_seconds=5444.0)
mcs.impulsive_burn(dv=[0.5, 0, 0])
mcs.target_sequence(endpoint_path='Satellite/Sat2')
mcs.run()
mcs.apply_changes()
mcs.reset_profiles()
```

### ReportExporter — 报告导出

```python
from atk.component.reports import ReportExporter

report = ReportExporter(session, sat_obj, 'J2000 Position Velocity',
                        '1 Jan 2024 00:00:00.000', '7 Jan 2024 00:00:00.000')
path = report.to_file('output.csv')  # 导出到文件
path = report.to_data()              # 使用 ATK 默认输出路径
```

### 使用示例

```python
from atk.component import component_session
from atk.component.satellite import SatelliteBuilder
from atk.component.mcs import McsBuilder

with component_session() as session:
    scenario = session.new_scenario('MyScenario')
    scenario.set_analysis_period('1 Jan 2024', '7 Jan 2024')

    sat_obj = session.create_satellite('Sat1')
    sat = SatelliteBuilder(sat_obj)
    sat.set_propagator_type('PropagatorAstromaster')

    driver = sat.get_mcs_driver()
    mcs = McsBuilder(driver)
    mcs.initial_state_keplerian(sma=6678, ecc=0, inc=28.5, raan=0, argp=0, ta=0)
    mcs.propagate_duration(duration_seconds=5444.0)
    mcs.run()

    # 导出报告
    path = session.output_report(
        sat_obj, 'J2000 Position Velocity',
        '1 Jan 2024 00:00:00.000', '7 Jan 2024 00:00:00.000'
    )
    print(f"Report: {path}")
```

详见 [快速开始](../guides/getting-started.md)。

## 底层依赖

Component 模式底层依赖 ATK 官方的 `ATKComponentPythonModule`（SWIG 封装），提供：

- **IAtkObjectRoot**：根对象，Component 入口
- **IScenario**：场景对象
- **ISatellite**：卫星对象
- **IVADriverMCS**：MCS 驱动器
- **IAtkObjectCollection**：对象集合
- **IAnimation**：仿真动画控制

如需深入了解 ATK Component 接口的详细用法，参考 ATK 官方文档：
**https://gitcode.com/jinke18/atk-doc** — `二次开发教程/4-二次开发COMPONENT模式/`

## 与 Connect 模式对比

| 特性 | Component 模式 | Connect 模式 |
|------|---------------|--------------|
| 需要 ATK 软件运行 | 否 | 是 |
| 部署方式 | DLL 直接加载 | TCP 网络连接 |
| API 风格 | 面向对象方法调用 | 命令字符串 |
| 适用场景 | 自动化、无图形界面 | 远程控制、有图形界面 |
| 性能 | 更快（无网络开销） | 依赖网络延迟 |
| 地面站/传感器 | 未实现 | FacilityBuilder + SensorBuilder |
| 覆盖分析 | 未实现 | CoverageBuilder |
| 星座模式 | 未实现 | WalkerBuilder |
