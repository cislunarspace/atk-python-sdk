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
              │                              │
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
| `create_satellite(name)` | 创建卫星 |
| `get_object(path)` | 按路径获取对象 |

### SatelliteBuilder — 卫星配置

```python
from atk.component.satellite import SatelliteBuilder

sat = SatelliteBuilder(sat_obj)
sat.set_propagator_type('PropagatorAstromaster')
driver = sat.get_mcs_driver()
```

### McsBuilder — 机动序列构建

```python
from atk.component.mcs import McsBuilder

mcs = McsBuilder(driver)
mcs.initial_state_keplerian(sma=6678, ecc=0, inc=28.5, raan=0, argp=0, ta=0)
mcs.propagate_duration(duration_seconds=5444.0)
mcs.run()
```

### 使用示例

```python
from atk.component import component_session
from atk.component.satellite import SatelliteBuilder
from atk.component.mcs import McsBuilder

with component_session() as session:
    scenario = session.new_scenario('MyScenario')
    scenario.set_analysis_period('1 Jan 2024', '7 Jan 2024')

    sat_obj = scenario.create_satellite('Sat1')
    sat = SatelliteBuilder(sat_obj)
    sat.set_propagator_type('PropagatorAstromaster')

    driver = sat.get_mcs_driver()
    mcs = McsBuilder(driver)
    mcs.initial_state_keplerian(sma=6678, ecc=0, inc=28.5, raan=0, argp=0, ta=0)
    mcs.run()
```

详见 [快速开始](../guides/getting-started.md)。

## 底层依赖

Component 模式底层依赖 ATK 官方的 `ATKComponentPythonModule`（SWIG 封装），提供：

- **IAtkObjectRoot**：根对象，Component 入口
- **IScenario**：场景对象
- **ISatellite**：卫星对象
- **IAtkObjectCollection**：对象集合

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
