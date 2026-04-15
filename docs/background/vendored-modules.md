# Vendored 模块

## 概述

`vendored/` 目录包含 ATK 官方提供的 SWIG 绑定文件。这些文件是 ATK SDK 的一部分，本项目将其复制到源码树中以确保可移植性和构建确定性。

## 目录结构

```
vendored/
├── ATKConnectModule.py          # Connect 模式 Python 包装
├── _ATKConnectModule.pyd        # Windows 原生 DLL
├── _ATKConnectModule.so         # Linux 原生 DLL
└── ATKComponentPythonModule.py   # Component 模式 Python 包装
```

## ATKConnectModule.py

这是 Connect 模式的 Python 包装模块，提供 `atkOpen`、`atkConnect`、`atkClose` 函数。

### 核心函数

```python
import ATKConnectModule

# 建立连接
conID = ATKConnectModule.atkOpen('127.0.0.1', 6655)

# 发送命令
result = ATKConnectModule.atkConnect(conID, 'New', '/', 'Scenario Scenario1')

# 关闭连接
ATKConnectModule.atkClose(conID)
```

### 返回值

`atkConnect` 可能返回两种类型：

1. **`str`** — 简单命令的响应（如 `"ACK"`、`"NACK"`）
2. **`CMDRESULT`** — 复杂命令（如报告）的响应对象

| 属性/方法 | 说明 |
|-----------|------|
| `m_vectData` | 空格分隔的结果字符串（仅 CMDRESULT） |
| `Item(i)` | 按索引访问（零基，仅 CMDRESULT） |

SDK 的 `ATKConnection.send()` 方法内部统一处理这两种返回类型，用户无需关心区别。

## ATKComponentPythonModule.py

这是 Component 模式的 SWIG 封装，提供 ATK 所有 COM 接口的 Python 绑定。

### 核心类

| 类名 | 说明 |
|------|------|
| `IAtkObjectRoot` | 根对象，Component 模式入口 |
| `IScenario` | 场景对象 |
| `ISatellite` | 卫星对象 |
| `IAtkObjectCollection` | 对象集合 |
| `IAnimation` | 仿真动画控制 |

### 枚举类型

| 枚举名 | 说明 |
|--------|------|
| `eScenario` | 场景类型 |
| `eSatellite` | 卫星类型 |
| `eFacility` | 地面站类型 |
| `ePropagatorTwoBody` | 二体传播器 |
| `ePropagatorJ2Perturbation` | J2 摄动传播器 |
| `ePropagatorAstromaster` | Astromaster 传播器 |

## 模块发现机制

当用户导入这些模块时，SDK 按以下顺序查找：

### Connect 模式

1. 检查 `sys.path` 中是否已有 `ATKConnectModule`
2. 查找与 `atk/` 同级的 `vendored/` 目录
3. 添加到 `sys.path` 并重新导入

### Component 模式

1. 检查 `sys.path` 中是否已有 `ATKComponentPythonModule`
2. 查找以下位置：
   - 项目 `vendored/` 目录
   - 项目根目录
   - `ATK_ROOT` 环境变量指定的路径

## ATK_ROOT 环境变量

如果 ATK 安装在非标准位置，设置 `ATK_ROOT` 环境变量：

```bash
# Windows
set ATK_ROOT=C:\Program Files\ATK\ATK-v4.0

# Linux
export ATK_ROOT=/opt/ATK/ATK-v4.0
```

SDK 会自动在 `ATK_ROOT` 目录下查找 `ATKComponentPythonModule.py`。

## 类型存根文件

`src/atk/connect/session.pyi` 为 `ATKConnection` 提供类型提示，包括通过猴子补丁注入的工厂方法。这使得 IDE 能正确提供自动补全：

- `create_scenario()`
- `create_satellite()`
- `create_facility()`
- `mcs_builder()`
- `create_coverage()`
- `constellation_builder()`
- `quick_report()`
- `report_rm()`
- `send_str()`

## 版本兼容性

Vendored 模块应与 ATK 软件版本匹配：

| ATK 版本 | SDK 版本 |
|----------|----------|
| ATK v4.0 | SDK 0.1.0+ |
| ATK v3.x | SDK 0.0.x |

升级 ATK 软件时，应同步更新 `vendored/` 目录中的文件。

## 故障排查

### ATKConnectModule 导入失败

```
ImportError: ATKConnectModule not found in src/vendored/
```

**解决方法**：确保使用 `pip install -e .` 安装 SDK，这会将 `vendored/` 目录添加到 `sys.path`。

### Component 模块导入失败

```
ATKComponentError: ATKComponentPythonModule not found
```

**解决方法**：
1. 确保 `ATKComponentPythonModule.py` 和 `_ATKComponentPythonModule.pyd` 在搜索路径中
2. 设置 `ATK_ROOT` 环境变量指向 ATK 安装目录
3. 或将这两个文件复制到项目的 `vendored/` 目录
