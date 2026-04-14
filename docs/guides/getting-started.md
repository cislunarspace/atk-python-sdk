# 快速开始

## 安装

### 基本安装

```bash
pip install -e .
```

这会安装 `atk` 包并使其 `vendored/` 目录可导入。

### 开发安装

```bash
pip install -e ".[dev]"
```

这会额外安装测试依赖。

## Connect 模式快速开始

Connect 模式需要 ATK 软件在后台运行。

### 前提条件

1. 安装 ATK 软件
2. 启动 ATK（无需打开任何场景）
3. 确保 ATK 监听 `127.0.0.1:6655`

### 基本用法

```python
from atk.connect import connect

# 使用上下文管理器
with connect() as atk:
    # 新建场景
    scenario = atk.create_scenario('MyScenario')
    scenario.set_analysis_period('1 Jan 2024 00:00:00.000', '7 Jan 2024 00:00:00.000')

    # 新建卫星
    sat = atk.create_satellite('Sat1')
    sat.set_propagator('PropagatorAstromaster')

    # 设置轨道根数（开普勒根数）
    sat.set_keplerian(
        sma=7100,      # 半长轴 (km)
        ecc=0.001,     # 离心率
        inc=30,        # 倾角 (deg)
        raan=0,        # 升交点赤经 (deg)
        argp=0,        # 近地点幅角 (deg)
        ta=0           # 真近点角 (deg)
    )

    # 运行 MCS
    sat.run_mcs()

    # 保存场景
    scenario.save()
```

### 完整示例：霍曼转移

```python
from atk.connect import connect

def hohmann_transfer():
    with connect() as atk:
        # 创建场景
        scenario = atk.create_scenario('HohmannTransfer')
        scenario.set_analysis_period(
            '1 Jan 2024 00:00:00.000',
            '2 Jan 2024 00:00:00.000'
        )

        # 创建卫星
        sat = atk.create_satellite('TransferVehicle')
        sat.set_propagator('PropagatorAstromaster')

        # 构建 MCS
        mcs = atk.mcs_builder('*/Satellite/TransferVehicle')

        # 初始轨道
        mcs.initial_state_keplerian(
            sma=6678.0, ecc=0.0, inc=0.0,
            raan=0.0, argp=0.0, ta=0.0,
            epoch='1 Jan 2024 00:00:00.000'
        )

        # 滑行半周期
        mcs.propagate_duration(duration_seconds=5444.0, time_step=60.0)

        # 第一次脉冲
        mcs.impulsive_burn(dv=[0.1, 0.0, 0.0], burn_direction=' Velocity')

        # 滑行到目标
        mcs.propagate_duration(duration_seconds=5444.0, time_step=60.0)

        # 第二次脉冲
        mcs.impulsive_burn(dv=[0.1, 0.0, 0.0], burn_direction=' Velocity')

        # 运行
        mcs.run()
        mcs.apply_changes()

        scenario.save()
        print('霍曼转移完成')
```

## Component 模式快速开始

Component 模式直接加载 ATK DLL，无需 ATK 软件运行。

### 前提条件

1. 安装 ATK 软件
2. 将 `ATKComponentPythonModule.py` 和 `_ATKComponentPythonModule.pyd` 复制到 `vendored/` 目录
3. 或设置 `ATK_ROOT` 环境变量

### 基本用法

```python
from atk.component import component_session
from atk.component.satellite import SatelliteBuilder
from atk.component.mcs import McsBuilder

with component_session() as session:
    # 新建场景
    scenario = session.new_scenario('MyScenario')
    scenario.set_analysis_period('1 Jan 2024 00:00:00.000', '7 Jan 2024 00:00:00.000')

    # 创建卫星
    sat_obj = scenario.create_satellite('Sat1')
    sat = SatelliteBuilder(sat_obj)
    sat.set_propagator_type('PropagatorAstromaster')

    # 构建 MCS
    driver = sat.get_mcs_driver()
    mcs = McsBuilder(driver)
    mcs.initial_state_keplerian(
        sma=6678.0, ecc=0.0, inc=28.5,
        raan=0.0, argp=0.0, ta=0.0
    )
    mcs.propagate_duration(duration_seconds=5444.0)
    mcs.run()
```

## 选择模式

| 场景 | 推荐模式 |
|------|----------|
| 需要 ATK 图形界面 | Connect |
| 批量处理/自动化 | Component |
| 远程控制 ATK | Connect |
| 无图形界面环境 | Component |
| 性能敏感 | Component |

## 下一步

- [轨道力学基础](./orbital-mechanics-primer.md) — 理解示例代码中的公式
- [ATK Connect 命令](../reference/atk-commands.md) — Connect 命令详细参考
- [ATK 对象模型](../background/atk-object-model.md) — 对象层次结构
