# 轨道力学基础

## 开普勒轨道根数

卫星轨道通常用六个开普勒根数描述：

| 根数 | 符号 | 单位 | 说明 |
|------|------|------|------|
| 半长轴 | SMA (a) | km | 椭圆轨道长轴的一半 |
| 离心率 | ECC (e) | - | 轨道扁平程度，0=圆，<1=椭圆 |
| 倾角 | INC (i) | deg | 轨道平面与赤道面夹角 |
| 升交点赤经 | RAAN (Ω) | deg | 升交点在 J2000 坐标系中的经度 |
| 近地点幅角 | ARGP (ω) | deg | 近地点在轨道平面中的角度 |
| 真近点角 | TA (ν) | deg | 卫星在轨道中当前位置 |

### 半长轴与轨道周期

半长轴决定了轨道周期（对于圆轨道）：

```
T = 2π × √(a³ / μ)
```

其中：
- `T` — 轨道周期（秒）
- `a` — 半长轴（km）
- `μ` — 地球引力常数 ≈ 398600.4418 km³/s²

### 示例：ISS 轨道周期

```python
import math

mu = 398600.4418  # km³/s²
a_iss = 6778.0    # km (ISS 约 410 km  altitude)

T = 2 * math.pi * math.sqrt(a_iss**3 / mu)
print(f"ISS 周期: {T:.0f} 秒 = {T/60:.1f} 分钟")
# ISS 周期约 92 分钟
```

## 二体运动

最简单的轨道运动模型，假设地球为点质量。

### 位置速度计算

对于给定时刻的真近点角，可以计算卫星的位置和速度：

```python
import math

def keplerian_to_state(sma, ecc, inc, raan, argp, ta, mu=398600.4418):
    """
    将开普勒根数转换为笛卡尔位置速度

    返回: (x, y, z, vx, vy, vz) in km 和 km/s
    """
    # 轨道角动量
    h = math.sqrt(mu * sma * (1 - ecc**2))

    # 在轨道平面内的位置
    r = h**2 / mu / (1 + ecc * math.cos(math.radians(ta)))

    x_orb = r * math.cos(math.radians(ta))
    y_orb = r * math.sin(math.radians(ta))

    # 在轨道平面内的速度
    vr = mu / h * ecc * math.sin(math.radians(ta))
    vtheta = mu / h * (1 + ecc * math.cos(math.radians(ta)))

    vx_orb = vr * math.cos(math.radians(ta)) - vtheta * math.sin(math.radians(ta))
    vy_orb = vr * math.sin(math.radians(ta)) + vtheta * math.cos(math.radians(ta))

    # 转换到 J2000 坐标系（简化版本）
    # 需要完整的欧拉角旋转矩阵
    # ...
```

## 霍曼转移

霍曼转移是最基本的轨道机动方式，使用两次脉冲发动机。

### 原理

1. 在圆轨道上加速（第一次脉冲）→ 椭圆转移轨道
2. 在椭圆轨道远地点再次加速（第二次脉冲）→ 目标圆轨道

### 转移轨道参数

```python
import math

def hohmann_transfer(r1, r2, mu=398600.4418):
    """
    计算霍曼转移参数

    参数:
        r1: 初始轨道半径 (km)
        r2: 目标轨道半径 (km)

    返回: (dv1, dv2, transfer_period)
    """
    # 半长轴
    a_transfer = (r1 + r2) / 2

    # 转移轨道周期
    T_transfer = 2 * math.pi * math.sqrt(a_transfer**3 / mu)

    # 第一次脉冲速度增量
    v1_circular = math.sqrt(mu / r1)
    v1_elliptic = math.sqrt(mu * (2/r1 - 1/a_transfer))
    dv1 = v1_elliptic - v1_circular

    # 第二次脉冲速度增量
    v2_circular = math.sqrt(mu / r2)
    v2_elliptic = math.sqrt(mu * (2/r2 - 1/a_transfer))
    dv2 = v2_circular - v2_elliptic

    return dv1, dv2, T_transfer / 2  # 转移时间是半周期
```

### 示例：LEO 到 GEO

```python
r_leo = 6778.0      # ISS 轨道 (km)
r_geo = 42164.197   # 地球同步轨道 (km)

dv1, dv2, t_transfer = hohmann_transfer(r_leo, r_geo)
print(f"第一次脉冲: {dv1:.2f} m/s")
print(f"第二次脉冲: {dv2:.2f} m/s")
print(f"转移时间: {t_transfer/3600:.1f} 小时")
```

### 在 ATK 中实现

```python
# 初始轨道
mcs.initial_state_keplerian(
    sma=6678.0, ecc=0.0, inc=0.0,
    raan=0.0, argp=0.0, ta=0.0,
    epoch='1 Jan 2024 00:00:00.000'
)

# 半周期滑行
T_half = 5444.0  # 约 90 分钟
mcs.propagate_duration(duration_seconds=T_half, time_step=60.0)

# 第一次脉冲（在近地点）
mcs.impulsive_burn(dv=[dv1, 0.0, 0.0], burn_direction=' Velocity')

# 半周期滑行到远地点
mcs.propagate_duration(duration_seconds=T_half, time_step=60.0)

# 第二次脉冲（在远地点）
mcs.impulsive_burn(dv=[dv2, 0.0, 0.0], burn_direction=' Velocity')
```

## 坐标系统

### J2000 (ECI)

地球惯性坐标系，原点在地心，X 轴指向 J2000 历元的春分点。

- 适用于描述卫星轨道
- 不随地球自转

### ECF (Earth-Centered Fixed)

地球固定坐标系，随地球自转。

- 适用于描述地面站位置
- 经纬度坐标

### 坐标转换

```python
def eci_to_ecf(x_eci, y_eci, z_eci, gast):
    """
    ECI 到 ECF 转换

    参数:
        x_eci, y_eci, z_eci: ECI 位置 (km)
        gast: 春分点时角 (deg)

    返回: (x_ecf, y_ecf, z_ecf)
    """
    gast_rad = math.radians(gast)
    x_ecf = x_eci * math.cos(gast_rad) + y_eci * math.sin(gast_rad)
    y_ecf = -x_eci * math.sin(gast_rad) + y_eci * math.cos(gast_rad)
    z_ecf = z_eci
    return x_ecf, y_ecf, z_ecf
```

## ATK 中的传播器

ATK 支持多种轨道传播模型：

| 传播器 | 说明 | 适用场景 |
|--------|------|----------|
| TwoBody | 二体运动 | 初轨计算、演示 |
| J2Perturbation | J2 摄动 | 低轨卫星 |
| HPOP | 高精度轨道传播 | 精密轨道确定 |
| SGP4 | TLE 传播 | 编目卫星 |
| Astromaster | Astromaster | 专业任务分析 |

### 选择传播器

```python
# 低轨卫星，考虑 J2 摄动
sat.set_propagator('PropagatorJ2Perturbation')

# 高轨或地球同步
sat.set_propagator('PropagatorAstromaster')

# TLE 数据
sat.set_propagator('PropagatorSGP4')
```
