# ATK 对象模型

## 概述

ATK 采用层次化的对象模型，所有对象都挂在场景（Scenario）根节点下。

```
场景根目录 (/)
├── Satellite/          # 卫星
│   └── Satellite1
│       ├── Sensor/      # 敏感器
│       │   └── Sensor1
│       ├── Transmitter/ # 发射器
│       └── Receiver/    # 接收器
├── Facility/           # 地面设施
│   └── GroundStation
├── CoverageDefinition/ # 覆盖定义
│   └── Coverage1
├── Aircraft/           # 飞机
├── Ship/               # 船
├── Vehicle/            # 车辆
├── Missile/            # 导弹
├── Rocket/             # 火箭
├── Star/               # 恒星
├── Planet/             # 行星
└── Chain/              # 链
```

## 对象类型

### 场景 (Scenario)

场景是 ATK 最高级别的容器，包含所有其他对象。

**对象路径**：`/Scenario/ScenarioName` 或简写 `/`

**主要属性**：
- 分析时间段（开始时间、结束时间）
- 仿真模式

### 卫星 (Satellite)

卫星是航天任务分析的核心对象，用于轨道传播和机动规划。

**对象路径**：`*/Satellite/SatelliteName`

**主要子对象**：
- Sensor（敏感器）
- Transmitter（发射器）
- Receiver（接收器）

### 地面站 (Facility)

地面站是固定位置的地面目标。

**对象路径**：`*/Facility/FacilityName`

### 覆盖定义 (CoverageDefinition)

用于分析卫星对地面或空间的覆盖性能。

**对象路径**：`*/CoverageDefinition/CoverageName`

### 链 (Chain)

链用于定义对象之间的可见性关系。

**对象路径**：`*/Chain/ChainName`

## 对象路径格式

### 基本格式

```
*/<Class>/<InstanceName>
```

| 部分 | 说明 | 示例 |
|------|------|------|
| `*` | 通配符，表示任意场景 | `*` |
| `<Class>` | 对象类名 | `Satellite`, `Facility` |
| `<InstanceName>` | 对象实例名 | `Sat1`, `GroundStation` |

### 嵌套路径

子对象的路径格式：

```
*/Satellite/Sat1/Sensor/Sensor1
```

### 省略通配符

Connect 命令中可以使用简化的路径格式：

```connect
New / */Satellite Satellite1
New / Satellite Satellite1
```

SDK 会自动规范化为 `*/Satellite/Satellite1`。

## 属性路径

对象属性通过长路径格式访问：

```
*/Satellite/Sat1/MainSequence.SegmentList.Initial_State.InitialState.Keplerian.sma
```

| 段 | 说明 |
|----|------|
| `MainSequence` | 主序列 |
| `SegmentList` | 段列表 |
| `Initial_State` | 初始状态段 |
| `InitialState.Keplerian` | 初始状态的 Kepler 参数 |
| `sma` | 半长轴 |

## 对象类名

| 中文 | Connect 命令类名 | Component 枚举值 |
|------|-----------------|-----------------|
| 场景 | `Scenario` | `eScenario` |
| 卫星 | `Satellite` | `eSatellite` |
| 地面站 | `Facility` | `eFacility` |
| 敏感器 | `Sensor` | `eSensor` |
| 发射器 | `Transmitter` | `eTransmitter` |
| 接收器 | `Receiver` | `eReceiver` |
| 链 | `Chain` | `eChain` |
| 飞机 | `Aircraft` | `eAircraft` |
| 船 | `Ship` | `eShip` |
| 车辆 | `Vehicle` | `eVehicle` |
| 导弹 | `Missile` | `eMissile` |
| 火箭 | `Rocket` | `eRocket` |
| 恒星 | `Star` | `eStar` |
| 行星 | `Planet` | `ePlanet` |

## 创建对象

### Connect 模式

```connect
New / Scenario ScenarioName
New / */Satellite Satellite1
New / */Facility GroundStation
New / */Satellite/Satellite1/Sensor Sensor1
```

### Component 模式

```cpp
IAtkObjectCollection* pIAtkObjColl = pIScen->GetChildren();
ISatellite* pISate = (ISatellite*)pIAtkObjColl->New(eSatellite, "Satellite1");
```

## 获取对象

### Connect 模式

```python
# 获取所有实例名
result = atkConnect(conID, 'AllInstanceNames', '/', '')
```

### Component 模式

```cpp
ISatellite* pISate = (ISatellite*)pIAORoot->GetObjectFromPath("Satellite/Satellite1");
bool bRet = pIAORoot->ObjectExists("Satellite/Satellite1");
```

## 删除对象

### Connect 模式

```connect
Unload / */Satellite/Satellite1
UnloadMulti / */Facility/Fac*
```

### Component 模式

```cpp
pISate->Unload();
```
