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
              │  mcs_builder()               │
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
```

### ATKConnection 主要方法

| 方法 | 说明 |
|------|------|
| `create_scenario(name)` | 创建场景，返回 `ScenarioBuilder` |
| `create_satellite(name)` | 创建卫星，返回 `SatelliteBuilder` |
| `create_coverage(name)` | 创建覆盖分析，返回 `CoverageBuilder` |
| `mcs_builder(satellite_path)` | 创建 MCS 构建器，返回 `McsBuilder` |
| `send(command, obj_path, param)` | 发送原生 Connect 命令 |

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

    # 保存场景
    scenario.save()
```

详见 [快速开始](../guides/getting-started.md)。

## 底层依赖

Connect 模式底层依赖 ATK 官方的 `ATKConnectModule`，提供三个原生函数：

| 函数 | 说明 |
|------|------|
| `atkOpen(host, port)` | 建立 TCP 连接 |
| `atkConnect(conID, cmd, path, param)` | 发送 Connect 命令 |
| `atkClose(conID)` | 关闭连接 |

如需深入了解 Connect 命令格式和协议，参考 ATK 官方文档：
**https://gitcode.com/jinke18/atk-doc** — `二次开发教程/2-二次开发CONNECT模式/`
