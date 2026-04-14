# 时间和单位

## ATK 时间格式

ATK 使用特定格式的时间字符串，主要有以下几种：

### 完整日期时间格式

```
"5 Nov 2022 00:00:00.000"
```

格式说明：
- `5` — 日期（1-31）
- `Nov` — 月份（三字母英文缩写）
- `2022` — 年份（四位数）
- `00:00:00.000` — 时:分:秒.毫秒

### 无毫秒格式

```
"5 Nov 2022 00:00:00"
```

### 短日期格式

```
"5 Nov 2022"
```

### 其他支持格式

ATK 还支持以下格式：

| 格式 | 示例 |
|------|------|
| ISO 格式 | `"2023-07-29 09:19:01.000"` |
| 月年格式 | `"Nov 2022"` |

## SDK 时间处理

### 解析 ATK 时间字符串

```python
from atk.utils import parse_atk_time
from datetime import datetime

dt = parse_atk_time("5 Nov 2022 00:00:00.000")
# → datetime(2022, 11, 5, 0, 0, 0, 0)
```

### 格式化 ATK 时间字符串

```python
from atk.utils import format_atk_time
from datetime import datetime

dt = datetime(2022, 11, 5, 0, 0, 0, 0)
time_str = format_atk_time(dt)
# → "5 Nov 2022 00:00:00.000"
```

### 支持的解析格式

| 格式 | 示例 | 解析结果 |
|------|------|----------|
| `dd Mon yyyy HH:mm:ss.fff` | `"5 Nov 2022 00:00:00.000"` | 完整解析 |
| `dd Mon yyyy HH:mm:ss` | `"5 Nov 2022 00:00:00"` | 无毫秒 |
| `dd Mon yyyy` | `"5 Nov 2022"` | 仅日期 |
| `yyyy-mm-dd HH:mm:ss.fff` | `"2023-07-29 09:19:01.000"` | ISO 变体 |
| `Mon yyyy` | `"Nov 2022"` | 仅年月 |

## ATK 单位制

### Connect 模式单位设置

```connect
Units_SetConnect / Date "JDate"           # 日期格式
Units_SetConnect / Distance km             # 距离单位
Units_SetConnect / Time sec               # 时间单位
Units_SetConnect / Angle deg              # 角度单位
```

### 默认单位

Connect 模式的默认单位：

| 维度 | 默认单位 | 说明 |
|------|----------|------|
| 距离 | km | 千米 |
| 时间 | sec | 秒 |
| 角度 | deg | 度 |
| 速度 | km/s | 千米每秒 |

### 轨道参数单位

| 参数 | 单位 | 说明 |
|------|------|------|
| 半长轴 (SMA) | km | 千米 |
| 离心率 (ECC) | - | 无量纲，0≤e<1 |
| 倾角 (INC) | deg | 度 |
| 升交点赤经 (RAAN) | deg | 度 |
| 近地点幅角 (ARGP) | deg | 度 |
| 真近点角 (TA) | deg | 度 |
| 位置 (x,y,z) | km | 千米 |
| 速度 (vx,vy,vz) | km/s | 千米每秒 |

### 时间单位

| 单位 | 说明 |
|------|------|
| sec | 秒 |
| min | 分钟 |
| hr | 小时 |
| day | 天 |

## 坐标系

### 常用坐标系

| 坐标系 | 说明 |
|--------|------|
| J2000 | J2000 惯性坐标系 |
| ECF | 地球固定坐标系 |
| ECI | 地球惯性坐标系 |
| CBF | 卫星本体坐标系 |

### 坐标转换

ATK 支持在不同坐标系之间进行位置和速度向量的转换：

```connect
# 设置 ECI 位置
SetPosition */Satellite/Sat1 ECI "1 Jul 2021 09:00:00.000" x y z vx vy vz

# 设置 LLA 位置（纬经高）
SetPosition */Satellite/Sat1 LLA "1 Jul 2021 09:00:00.000" lat lon alt
```

## 仿真时间

### 场景时间设置

```python
# Connect 模式
scenario.set_analysis_period("1 Jan 2024 00:00:00.000", "7 Jan 2024 00:00:00.000")

# Component 模式
scenario.SetTimePeriod("1 Jan 2024 00:00:00.000", "7 Jan 2024 00:00:00.000")
```

### 仿真步长

| 模式 | 说明 | 示例值 |
|------|------|--------|
| 步长模式 | 每步推进的时间 | 10（秒） |
| 倍率模式 | 实时倍速 | 128 |
| 实时模式 | 与系统时间同步 | - |

### 仿真控制命令

```connect
Animate * Start                      # 开始仿真
Animate * Pause                      # 暂停仿真
Animate * Reset                      # 重置仿真
Animate * Faster                     # 加速
Animate * Slower                     # 减速
```
