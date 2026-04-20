# 快速开始

## 安装

### 基本安装

```bash
uv sync
```

这会安装 `atk` 包并使其 `vendored/` 目录可导入。

### 开发安装

```bash
uv sync --dev
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

### 创建地面站和传感器

```python
with connect() as atk:
    scenario = atk.create_scenario('SensorDemo')
    scenario.set_analysis_period('1 Jan 2024', '7 Jan 2024')

    # 创建地面站
    facility = atk.create_facility('Beijing', lat=39.9, lon=116.4, height=50)

    # 在地面站下创建传感器（一步完成）
    sensor = facility.create_sensor('TrackingSensor',
        el_start=5, el_end=85,     # 俯仰角范围 (deg)
        az_start=0, az_end=360,    # 方位角范围 (deg)
        max_range=2000             # 最大作用距离 (km)
    )

    # 创建卫星并设置 TLE 轨道
    sat = atk.create_satellite('ISS')
    sat.set_state_tle(
        line1='1 25544U 98067A   24001.50000000  .00016717  00000-0  10270-3 0  9000',
        line2='2 25544  51.6400 208.9163 0006703  44.2800 315.9700 15.49000000400000'
    )
```

### 查询报告

```python
with connect() as atk:
    # ... 创建卫星并运行 MCS ...

    # 快速报告
    result = atk.quick_report('*/Satellite/Sat1', 'Position', time_period='*')

    # 转换为 dict 列表
    rows = result.to_dict()

    # 转换为 pandas DataFrame（需要安装 pandas）
    df = result.to_dataframe()
    print(df.head())

    # Report_RM — 更详细的报告
    result = atk.report_rm('*/Satellite/Sat1',
                           style='J2000PositionVelocity',
                           time_period='1 Jan 2024 00:00:00.000 7 Jan 2024 00:00:00.000')
```

### 场景控制和动画

```python
with connect() as atk:
    scenario = atk.create_scenario('Demo')

    # 设置分析模式
    scenario.set_analysis_mode('Keplerian')

    # 控制动画
    scenario.animate(forward=True)
    scenario.stop_animation()

    # 打开图形窗口
    scenario.open_2d_window('2D View')
    scenario.open_3d_window('3D View')

    # 加载已有场景
    scenario.load('C:/ATK/Scenarios/MyScenario.xml')
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
    sat_obj = session.create_satellite('Sat1')
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

    # 导出报告
    path = session.output_report(
        sat_obj, 'J2000 Position Velocity',
        '1 Jan 2024 00:00:00.000', '7 Jan 2024 00:00:00.000'
    )
    print(f"Report: {path}")
```

### 使用笛卡尔坐标

```python
with component_session() as session:
    scenario = session.new_scenario('CartesianDemo')
    scenario.set_analysis_period('1 Jan 2024', '7 Jan 2024')

    sat_obj = session.create_satellite('Sat1')
    sat = SatelliteBuilder(sat_obj)
    sat.set_propagator_type('PropagatorTwoBody')

    # 使用笛卡尔坐标设置初始状态
    sat.set_cartesian(x=6678, y=0, z=0, vx=0, vy=7.73, vz=0)

    # 设置质量和颜色
    sat.set_mass(500)
    sat.set_color(12)
```

## 选择模式

| 场景 | 推荐模式 |
|------|----------|
| 需要 ATK 图形界面 | Connect |
| 批量处理/自动化 | Component |
| 远程控制 ATK | Connect |
| 无图形界面环境 | Component |
| 性能敏感 | Component |
| 需要地面站/传感器/覆盖分析 | Connect |

## 下一步

- [轨道力学基础](./orbital-mechanics-primer.md) — 理解示例代码中的公式
- [ATK Connect 命令](../reference/atk-commands.md) — Connect 命令详细参考
- [ATK 对象模型](../background/atk-object-model.md) — 对象层次结构
- [设计决策](../architecture/design-decisions.md) — 架构设计背后的理由
