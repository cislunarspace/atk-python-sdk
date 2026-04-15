# 设计决策

本文档记录 ATK Python SDK 中的关键设计决策及其背后的理由。

## 1. 双模式架构

### 决策

提供 Connect 模式和 Component 模式两种 API。

### 理由

| 模式 | 适用场景 |
|------|----------|
| Connect 模式 | 需要 ATK 图形界面、远程控制、与其他 Connect 客户端共享 ATK 实例 |
| Component 模式 | 自动化测试、批处理、无图形界面环境、性能敏感场景 |

ATK 用户场景差异大，双模式架构确保 SDK 覆盖所有主要使用方式。

## 2. 构建器模式 (Builder Pattern)

### 决策

使用 `ScenarioBuilder`、`SatelliteBuilder`、`McsBuilder` 等构建器类封装底层 Connect 命令。

### 理由

**问题**：Connect 命令是字符串格式，手动拼接容易出错：

```python
# 容易出错
conn.send("SetState", "*/Satellite/Sat1",
    f'Classical TwoBody "1 Jan 2024 00:00:00.000" "1 Jan 2024 00:00:00.000" '
    f'60 J2000 "1 Jan 2024 00:00:00.000" {sma} {ecc} {inc} {raan} {argp} {ta}')

# 构建器模式更清晰
sat.set_keplerian(sma=7100, ecc=0.001, inc=30, raan=0, argp=0, ta=0)
```

**收益**：
- 类型安全，参数验证
- 代码可读性强
- IDE 自动补全支持
- 减少命令格式错误

## 3. 上下文管理器 (Context Manager)

### 决策

所有连接会话使用上下文管理器：

```python
with connect() as atk:
    # 使用 atk 连接
# 自动关闭连接
```

### 理由

- 确保连接正确关闭，即使发生异常
- 资源管理更安全
- 代码更简洁

## 4. Vendored 模块策略

### 决策

将 ATK 官方 SWIG 绑定文件复制到 `vendored/` 目录，不直接依赖 ATK 安装路径。

### 理由

| 考量 | 说明 |
|------|------|
| 可移植性 | 不要求用户安装 ATK SDK |
| 版本隔离 | SDK 版本与 ATK 绑定版本绑定 |
| 构建确定性 | 绑定的 DLL/so 文件版本可控 |

## 5. 异常层次结构

### 决策

定义完整的异常类继承体系：

```
ATKError
├── ATKConnectionError
│   └── ATKConnectionTimeout
├── ATKCommandError
├── ATKObjectNotFoundError
├── ATKScenarioError
├── ATKSatelliteError
├── ATKMCSError
├── ATKReportError
├── ATKComponentError
└── ATKValueError
```

### 理由

- **精确错误处理**：调用方可以根据异常类型采取不同策略
- **调试友好**：特定异常包含相关上下文（如路径、命令参数）
- **不泄露 ATK 内部实现**：异常消息由 SDK 重新格式化

## 6. 时间格式处理

### 决策

在 `atk.utils` 模块中统一处理 ATK 时间格式解析和格式化。

### 理由

- ATK 时间格式多样：`"5 Nov 2022 00:00:00.000"`、`"2023-07-29 09:19:01.000"`
- 统一解析避免重复代码
- 集中维护，便于处理边界情况

## 7. 路径规范化

### 决策

提供 `resolve_path()`、`path_join()` 等路径辅助函数。

### 理由

- ATK 路径格式灵活：`*/Satellite/Sat1`、`Satellite/Sat1`、`/Satellite/Sat1` 均可
- 规范化后内部处理更简单
- 减少用户犯错机会

## 8. 重试机制

### 决策

连接失败时自动重试（默认 3 次，2 秒退避）。

### 理由

- ATK 服务可能未就绪
- 网络瞬时故障不导致整体失败
- 提升 SDK 在自动化场景中的鲁棒性

## 9. Component 模式的双入口点

### 决策

Component 模式同时支持 `component_session()` 上下文管理器和直接实例化 `ComponentSession`。

### 理由

- 上下文管理器适合简单场景
- 直接实例化适合复杂场景（需要保持根对象引用）
- API 灵活性与简洁性兼得

## 10. 猴子补丁模式 (Monkey-Patching)

### 决策

每个 Connect 子模块（scenario、satellite、facility、mcs、coverage、constellation、reports）在导入时调用 `_patch_connection()`，向 `ATKConnection` 注入工厂方法。

### 理由

**问题**：如果所有工厂方法都在 `session.py` 中定义，会导致循环导入（session → satellite → session）和臃肿的 session 模块。

**解决方案**：

```python
# facility.py 末尾
def _patch_connection():
    from atk.connect import session as _s
    _s.ATKConnection.create_facility = create_facility

_patch_connection()
```

`connect/__init__.py` 导入所有子模块以触发补丁。这种模式将每个构建器的注册逻辑放在定义它的模块中，避免循环依赖。

## 11. Facility 和 Sensor 的组合关系

### 决策

`SensorBuilder` 通过 `FacilityBuilder.create_sensor()` 创建，传感器挂在地面站下（`*/Facility/{name}/Sensor/{sensor}`），而非独立的工厂方法。

### 理由

- ATK 对象模型中 Sensor 是 Facility 的子对象
- 传感器需要知道其父级地面站名称以构建正确路径
- 组合创建模式（一次调用完成创建+配置）简化常见操作
- 用户也可直接实例化 `SensorBuilder` 获得更细粒度的控制

## 12. 类型存根文件 (.pyi)

### 决策

使用 `session.pyi` 为猴子补丁注入的方法提供类型提示。

### 理由

- 猴子补丁的方法无法被 IDE 静态分析发现
- `.pyi` 存根文件让 IDE 能提供正确的自动补全和类型检查
- 所有注入的工厂方法（`create_scenario`、`create_facility`、`quick_report` 等）都在存根中声明

## 13. atkConnect 返回值的双重性

### 决策

`send()` 方法内部同时处理 `str` 和 `CMDRESULT` 两种返回类型。

### 理由

**问题**：SWIG DLL 的 `atkConnect()` 函数可能返回：

- `str`：如 `"ACK"`、`"NACK"` — 简单命令的响应
- `CMDRESULT`：带 `m_vectData` 属性 — 报告等复杂命令的响应

这在 ATK 的 SWIG 封装中是已知行为。SDK 在 `send()` 中统一处理，对上层 API 透明。
