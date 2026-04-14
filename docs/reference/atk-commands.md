# ATK Connect 命令参考

## 概述

Connect 命令是 ATK 提供的一种文本命令接口，通过 TCP 连接发送命令字符串来操作 ATK 内部对象。

## 命令格式

### 基本格式

```
Command <ApplicationPath> <ObjectPath> {Parameters}
```

### 参数分隔符

命令参数使用空格分隔，字符串参数使用引号：

```
SetValue */Satellite/Sat1 "Propagator" Astromaster
SetAnalysisTimePeriod * "1 Nov 2007 01:02:00.00" "1 Nov 2007 03:04:00.00"
```

## 场景命令

### New — 新建场景或对象

```connect
New <ApplicationPath> <ClassPath> <NewObjectName> {NewOptions}
```

| 选项 | 说明 |
|------|------|
| `NoDefault` | 不创建默认子对象 |
| `Ignore` | 忽略错误 |
| `CentralBody <CBName>` | 指定中心天体 |

**示例**：
```connect
New / Scenario Scenario1                    # 新建场景
New / */Satellite Satellite1                # 新建卫星
New / */Facility GroundStation CentralBody Earth  # 新建地面站
New / */Satellite/Satellite1/Sensor Sensor1 # 新建传感器
```

### Save — 保存场景

```connect
Save <ApplicationPath> <ObjectPath> ["<SaveInDirectory>"]
```

**示例**：
```connect
Save / *                                   # 保存当前场景
Save / * "C:/Users/Desktop/TestScen.xml"  # 另存为
```

### Load — 加载场景

```connect
Load <ApplicationPath> {<ClassPath> | VDF} "<FilePath>"
```

**示例**：
```connect
Load / Scenario "E:/ATK/Scenario1.xml"    # 加载场景文件
```

### SetAnalysisTimePeriod — 设置分析时段

```connect
SetAnalysisTimePeriod <ScenarioPath> {TimeInterval}
```

**示例**：
```connect
SetAnalysisTimePeriod * "1 Nov 2007 01:02:00.00" "1 Nov 2007 03:04:00.00"
```

## 仿真控制命令

### Animate — 仿真控制

```connect
Animate <ScenarioPath> {AnimateOption} <Parameters>
```

| 选项 | 说明 |
|------|------|
| `Start` | 开始仿真 |
| `Pause` | 暂停仿真 |
| `Reset` | 重置仿真 |
| `Faster` | 加速 |
| `Slower` | 减速 |

**示例**：
```connect
Animate * Start                            # 开始仿真
Animate * Pause                            # 暂停
Animate * Reset                            # 重置
```

### SetAnimation — 设置仿真参数

```connect
SetAnimation <ScenarioPath> {AnimateOption} <Parameters>
```

| 选项 | 说明 |
|------|------|
| `CurrentTime <TimeInstant>` | 设置当前时间 |
| `AnimationMode {Normal\|RealTime\|XRealTime}` | 设置仿真模式 |
| `TimeStep <Value>` | 设置步长 |

**示例**：
```connect
SetAnimation * AnimationMode XRealTime     # 设置为倍率模式
SetAnimation * TimeStep 60                 # 设置步长为 60 秒
```

## 卫星命令

### SetPropagator — 设置传播器

```connect
SetPropagator <SatellitePath> <PropagatorName>
```

**示例**：
```connect
SetPropagator */Satellite/Satellite1 Astromaster
SetPropagator */Satellite/Satellite1 TwoBody
```

### SetState — 设置轨道状态

```connect
SetState <SatellitePath> <StateType> <Parameters>
```

**开普勒根数格式**：
```connect
SetState */Satellite/Sat1 Classical TwoBody "1 Jan 2024 00:00:00.000" "1 Jan 2024 00:00:00.000" 60 J2000 "1 Jan 2024 00:00:00.000" 7100 0.001 30 0 0 0
```

参数格式：
```
Classical <Propagator> "<epoch>" "<stop>" <Step> <CoordSys> "<epoch>" <SMA> <ECC> <INC> <RAAN> <ARGP> <TA>
```

**笛卡尔坐标格式**：
```connect
SetState */Satellite/Sat1 Cartesian TwoBody "1 Jan 2024 00:00:00.000" "1 Jan 2024 00:00:00.000" 60 J2000 "1 Jan 2024 00:00:00.000" x y z vx vy vz
```

### SetValue — 设置属性值

```connect
SetValue <ObjectPath> "<PropertyPath>" <Value>
```

**示例**：
```connect
SetValue */Satellite/Sat1 "MainSequence.SegmentList.Initial_State.InitialState.Keplerian.sma" 7100
SetValue */Satellite/Sat1 "MassProperties.TotalMass" 500
```

### RunMCS — 运行 MCS

```connect
RunMCS <SatellitePath>
```

**示例**：
```connect
RunMCS */Satellite/Satellite1
```

## 报告命令

### Report_RM — 获取数据报告

```connect
Report_RM <ObjectPath> ({Option} <Value>)...
```

| 选项 | 说明 |
|------|------|
| `Style "<ReportStyleName>"` | 报告样式名称 |
| `TimePeriod "<Start>" "<Stop>"` | 分析时段 |
| `TimeStep <Value>` | 报告步长 |

**示例**：
```connect
Report_RM */Satellite/Satellite1 Style "Position" TimePeriod "2023-07-29 09:19:01.000" "2023-07-29 10:09:38.000"
Report_RM */Satellite/Satellite1 Style "J2000 Position Velocity" TimeStep 60
```

### Access — 可见性分析

```connect
Access <ObjectPath> <AccessObjectPath> {TimePeriod <StartTime> <StopTime>}
```

**示例**：
```connect
Access */Satellite/Satellite1 */Facility/GroundStation TimePeriod "14 Mar 2024 00:00:00.000" "15 Mar 2024 00:00:00.000"
```

## 覆盖分析命令

### Cov — 覆盖配置

```connect
Cov <CovDefnObjectPath> Asset <AssetObjectPath> {Action}
```

**示例**：
```connect
Cov */CoverageDefinition/Coverage1 Asset */Satellite/Satellite1 Assign
```

### Cov_RM — 获取覆盖报告

```connect
Cov_RM <ObjectPath> Access Compute "<ReportStyle>" [{TimeIntervals}]
```

**示例**：
```connect
Cov_RM */Satellite/Satellite1 Access Compute "Coverage" "14 Mar 2024 00:00:00.000" "15 Mar 2024 00:00:00.000"
```

## 对象操作命令

### Unload — 删除对象

```connect
Unload <ApplicationPath> <ObjectPath> [RemAssignedObjs]
```

**示例**：
```connect
Unload / */Satellite/Satellite1             # 删除卫星
Unload / *                                 # 关闭场景
```

### Rename — 重命名对象

```connect
Rename <ObjectPath> <NewName>
```

**示例**：
```connect
Rename */Satellite/Satellite1 Sat1
```

### Copy — 复制对象

```connect
Copy <ApplicationPath> <CopyFromObjectPath> [{CopyOption}]
```

**选项**：
- `Name <NewName>`：新对象名称
- `Path <NewObjectPath>`：新对象路径

**示例**：
```connect
Copy / Satellite/Satellite1 Name Satellite2
```

## 单位设置命令

### Units_SetConnect — 设置单位

```connect
Units_SetConnect <AppOrScenPath> {Default | {Dimension} {Unit}...}
```

**维度**：`Date`, `Distance`, `Time`, `Angle`

**示例**：
```connect
Units_SetConnect / Date JDate                        # 日期格式
Units_SetConnect / Distance km                       # 距离单位
Units_SetConnect / Time sec                          # 时间单位
```
