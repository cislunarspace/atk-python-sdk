# Plan: ATK Python SDK — Connect Mode + Component Mode

## Requirements Restatement

在当前仓库 (`atk-python-sdk`) 中，为 ATK 编写两个独立的高层次 Python SDK：

1. **Connect Mode SDK** (`atk.connect`)：依赖 ATK 软件窗口运行，通过 TCP 连接发送 Connect 命令字符串
2. **Component Mode SDK** (`atk.component`)：直接加载 ATK 原生 DLL，无需 ATK 软件窗口，通过 SWIG 封装的 OO 类操作

两个 SDK 面向相同的用户场景（轨道分析、星座设计、覆盖计算、MCS 机动规划），但 API 风格和适用环境不同。

---

## 核心区别

| | Connect Mode | Component Mode |
|--|--|--|
| **依赖** | 需要 ATK 软件运行 (`ATK.exe`) | 需要 ATK DLL，无需 ATK 进程 |
| **API 风格** | 字符串命令 `atkConnect(conID, 'SetValue', path, val)` | OO 类方法 `sat.SetPropagatorType(ePropagatorAstromaster)` |
| **适用平台** | Windows（Python 客户端连接 ATK） | Windows（Component Python 由 ATK 内嵌 Python 解释器运行） |
| **文件** | `ATKConnectModule.py`（已有）+ `atk/connect/` | `ATKComponentPythonModule.py`（已有）+ `atk/component/` |

---

## 文件结构（最终）

```
atk-python-sdk/
├── src/
│   ├── atk/                          # Python SDK 源码
│   │   ├── __init__.py
│   │   ├── exceptions.py
│   │   ├── utils.py
│   │   ├── connect/                 # Connect Mode SDK
│   │   │   ├── session.py
│   │   │   ├── scenario.py
│   │   │   ├── satellite.py
│   │   │   ├── mcs.py
│   │   │   ├── reports.py
│   │   │   ├── coverage.py
│   │   │   └── constellation.py
│   │   └── component/               # Component Mode SDK
│   │       ├── session.py
│   │       ├── scenario.py
│   │       ├── satellite.py
│   │       ├── mcs.py
│   │       └── reports.py
│   └── tests/                       # 测试（51 个测试）
│       ├── test_utils.py
│       └── connect/
│           ├── test_session.py
│           ├── test_scenario.py
│           ├── test_satellite.py
│           └── test_mcs.py
│
├── vendored/                        # ATK 提供的 SWIG 绑定
│   ├── __init__.py                  # 重导出 ATKConnectModule
│   ├── ATKConnectModule.py          # Connect 模式 Python 包装
│   ├── _ATKConnectModule.pyd        # Windows 原生 DLL
│   └── _ATKConnectModule.so         # Linux 原生 DLL
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

---

## 实现阶段

### Phase 1: 基础结构（Connect + Component 共用）

**创建文件：**
- `atk/__init__.py` — 包入口，模式自动检测或显式选择
- `atk/exceptions.py` — `ATKError`, `ATKConnectionError`, `ATKCommandError`, `ATKObjectNotFoundError`
- `atk/utils.py` — 时间字符串解析（Connect 格式 ↔ Python datetime）、路径解析（`*/Satellite/Sat1` 解析）

**Connect Mode 核心（`atk/connect/`）：**
- `session.py` — `ATKConnection` 类
  - `atkOpen()` → `conID`，带重试（3 次，2s 退避）
  - `atkConnect(conID, cmd, path, param)` → 解析 `CMDRESULT`
  - `atkClose(conID)`
  - 上下文管理器：`with connect('127.0.0.1', 6655) as atk:`

**Component Mode 核心（`atk/component/`）：**
- `session.py` — `ComponentSession` 类
  - `IAtkObjectRoot()` 初始化
  - `NewScenario(name)` → `IScenario`
  - `LoadScenario(path)` / `SaveScenario(path)`
  - `GetCurrentScenario()` → `IScenario`
  - `CloseScenario()`
  - 上下文管理器：`with component_session() as root:`

---

### Phase 2: Scenario 构建器

**Connect Mode** (`atk/connect/scenario.py`):
```python
scenario = atk.create_scenario('MyScenario')
scenario.set_time_period('5 Nov 2022 00:00:00.000', '8 Nov 2022 00:00:00.000')
scenario.save()
```
Connect 命令字符串：
- `New / Scenario ScenarioName`
- `SetAnalysisTimePeriod */Scenario/ScenarioName "StartTime" "StopTime"`

**Component Mode** (`atk/component/scenario.py`):
```python
scenario = root.new_scenario('MyScenario')
scenario.set_time_period('5 Nov 2022 00:00:00.000', '8 Nov 2022 00:00:00.000')
scenario.save()
```
Component 方法：`IScenario.SetTimePeriod(start, stop)`, `IScenario.SetStartTime()`, `IScenario.SaveScenario()`

---

### Phase 3: Satellite 工厂

**Connect Mode** (`atk/connect/satellite.py`):
```python
sat = atk.create_satellite('Sat1', propagator='PropagatorAstromaster')
sat.set_keplerian(sma=7100, ecc=0.001, inc=30, raan=0, argp=0, ta=0)
sat.set_mass(500)
```
Connect 命令：
- `New / */Satellite Sat1`
- `SetPropagator */Satellite/Sat1 PropagatorAstromaster`
- `SetValue */Satellite/Sat1 MainSequence.SegmentList.Initial_State.InitialState.Keplerian.sma 7100`

**Component Mode** (`atk/component/satellite.py`):
```python
satellite = scenario.create_satellite('Sat1')
satellite.set_propagator_type(ePropagatorAstromaster)
driver = satellite.get_mcs_driver()
segments = driver.get_main_sequence()
# ... 添加 MCS 段
driver.run_mcs()
```
Component 方法链：`IScenario.GetChildren().New(eSatellite, "Sat1")` → `ISatellite.SetPropagatorType()` → `ISatellite.GetPropagator()` → `IVADriverMCS`

---

### Phase 4: MCS (Mission Control Sequence) 机动序列构建器

**Connect Mode** (`atk/connect/mcs.py`):
```python
mcs = atk.mcs_builder('*/Satellite/Sat1')
mcs.initial_state_keplerian(sma=6678, ecc=0, inc=28.5, raan=0, argp=0, ta=0)
mcs.propagate_until('10 Jan 2024 12:00:00.000')
mcs.impulsive_burn(dv=[0.5, 0, 0])
mcs.run()
```

**Component Mode** (`atk/component/mcs.py`):
```python
mcs = McsBuilder(satellite)  # wraps IVADriverMCS
mcs.initial_state_keplerian(sma=6678, ecc=0, inc=28.5, raan=0, argp=0, ta=0)
mcs.propagate_until('10 Jan 2024 12:00:00.000')
mcs.impulsive_burn(dv=[0.5, 0, 0])
mcs.run()
```
Component 段类型：`IVAMCSSegmentCollection.AppendSegment()` + `IVAMCSSegmentProperties.Set*()`

---

### Phase 5: Report 执行与数据解析

**Connect Mode** (`atk/connect/reports.py`):
```python
result = atk.report_rm('*/Satellite/Sat1', style='Position', time='*')
df = result.to_dataframe()
```

**Component Mode** (`atk/component/reports.py`):
```python
path = root.output_data_report(satellite, 'J2000 Position Velocity', start, stop)
```

---

### Phase 6: Coverage 分析

**Connect Mode** (`atk/connect/coverage.py`):
```python
cov = atk.create_coverage('GroundCoverage')
cov.add_asset('*/Satellite/Sat1')
cov.add_facility('*/Facility/GroundStation')
cov.set_grid_resolution(lat_step=1.0, lon_step=1.0)
stats = cov.compute_stats()
```

---

### Phase 7: Constellation 批量操作

**Connect Mode** (`atk/connect/constellation.py`):
```python
walker = ConstellationBuilder(atk, 'Starlink')
walker.walker_delta(num_satellites=60, num_planes=6, inc=53, alt=550)
results = walker.run_mcs_parallel(jobs=8)
```

---

### Phase 8: 示例 + 测试

**Connect Mode 示例：**
- `examples/connect/hohmann_transfer.py` — 双脉冲霍曼转移
- `examples/connect/constellation_coverage.py` — Walker 星座覆盖分析

**Component Mode 示例：**
- `examples/component/hohmann_transfer.py` — Component 模式霍曼转移
- `examples/component/constellation_coverage.py` — Component 模式星座覆盖

**测试：** pytest，80% 覆盖率目标

---

## 技术要点

### Component Mode SWIG 绑定使用方式

```python
# ATKComponentPythonModule.py 和 _ATKComponentPythonModule.pyd
# 需要从 ATK 安装目录复制到 vendored/ 目录，或设置 ATK_ROOT 环境变量
from atk.component import session

with session() as s:
    s.root.NewScenario("Scenario1")
    # ...
```
pISatellite.SetPropagatorType(ATK.ePropagatorAstromaster)

# 获取 MCS Driver
pIVADriverMCS = pISatellite.GetPropagator()

# 运行
pIVADriverMCS.RunMCS()
pIVADriverMCS.ApplyAllProfileChanges()

# 保存
pIAORoot.SaveScenario("C:/temp/test.xml")
```

### Connect Mode 命令字符串特点

- 命令格式：`atkConnect(conID, 'Command', 'objPath', 'paramString')`
- 路径格式：`*/Satellite/Sat1`（`*` = 根场景）
- 属性路径很长：`MainSequence.SegmentList.Initial_State.InitialState.Keplerian.sma`
- 需要 builder 封装以避免手动拼接字符串错误

### Component vs Connect 对照

| 操作 | Connect 命令 | Component 方法 |
|------|------------|----------------|
| 新建场景 | `New / Scenario Name` | `root.NewScenario("Name")` |
| 创建卫星 | `New / */Satellite Sat1` | `scenario.GetChildren().New(eSatellite, "Sat1")` |
| 设置时间 | `SetAnalysisTimePeriod ...` | `scenario.SetTimePeriod(start, stop)` |
| 设置推进器 | `SetPropagator */... PropagatorAstromaster` | `sat.SetPropagatorType(ePropagatorAstromaster)` |
| 运行 MCS | `RunMCS */...` | `driver.RunMCS()` |
| 保存 | `Save */...` | `root.SaveScenario()` |

---

## 风险

| 风险 | 级别 | 缓解 |
|------|------|------|
| Component 模式的 `ATKComponentPythonModule.py` 是 SWIG 生成的大文件（440KB），需要从 ATK 目录复制到项目 | LOW | 直接复制，SWIG 封装保持不变 |
| Component Mode 需要 ATK 内嵌 Python 环境运行，不是标准 Python 环境 | MEDIUM | 示例脚本说明运行环境要求 |
| Connect 命令字符串格式有些未在文档中完整记录 | MEDIUM | 从文档示例和 `2-Connect命令库` 目录逐步覆盖 |
| Component Mode 的 `IVAMCSSegment.AppendSegment()` 等方法签名需验证 | MEDIUM | 参考文档 `4-卫星类.md` 和 ATK 示例脚本 |

---

## 确认

这个计划覆盖：
- ✅ Connect Mode SDK（`atk.connect`）— 需要 ATK 软件运行
- ✅ Component Mode SDK（`atk.component`）— 直接 DLL 加载，无需 ATK 窗口

---

## 实现状态: ✅ 全部完成

| Phase | 内容 | 状态 |
|-------|------|------|
| — | 仓库初始化（src-layout + vendored） | ✅ |
| 1 | exceptions, utils, Connect/Component Session | ✅ |
| 2 | ScenarioBuilder + SatelliteBuilder | ✅ |
| 3 | McsBuilder (Connect + Component) | ✅ |
| 4 | Reports + Coverage (Connect + Component) | ✅ |
| 5 | WalkerBuilder + 批量操作 (Connect) | ✅ |
| 6 | Examples | ✅ |
| 7 | Tests (51/51 通过) | ✅ |
