# ATK Python SDK — 项目规划

## 项目概述

ATK Python SDK 是 ATK (Aerospace Tool Kit) 的第三方 Python 二次开发库，提供双模式架构（Connect + Component）的高层次 API 封装。

- **Connect 模式**：通过 TCP 连接向运行中的 ATK GUI 发送 Connect 命令
- **Component 模式**：直接加载 ATK DLL，无需 GUI

## 当前版本：v0.1.0

### 已完成功能

| 模块 | 功能 | 状态 |
|------|------|------|
| **Core** | 异常层次结构 (`ATKError` 体系) | 已完成 |
| **Core** | 工具函数 (`utils.py` — 时间解析、路径操作、CMDRESULT 解析) | 已完成 |
| **Connect** | 会话管理 (`connect()` 上下文管理器 + `ATKConnectionManager`) | 已完成 |
| **Connect** | 场景构建器 (`ScenarioBuilder`) — 创建/保存/加载/卸载/分析模式/动画/窗口 | 已完成 |
| **Connect** | 卫星构建器 (`SatelliteBuilder`) — 开普勒/笛卡尔/TLE/质量/姿态/颜色 | 已完成 |
| **Connect** | 地面站构建器 (`FacilityBuilder`) — 创建/位置/颜色 | 已完成 |
| **Connect** | 传感器构建器 (`SensorBuilder`) — 创建/视场定义/指向/约束 | 已完成 |
| **Connect** | MCS 构建器 (`McsBuilder`) — 开普勒/笛卡尔初始状态/传播/脉冲/目标序列 | 已完成 |
| **Connect** | 覆盖分析 (`CoverageBuilder` + `CoverageStats`) | 已完成 |
| **Connect** | Walker 星座 (`WalkerBuilder`) — Walker Delta 模式生成 + 批量 MCS | 已完成 |
| **Connect** | 报告系统 (`ReportResult` / `QuickReport` / `ReportRM`) | 已完成 |
| **Connect** | 类型存根 (`session.pyi`) — 猴子补丁方法的 IDE 类型提示 | 已完成 |
| **Component** | 会话管理 (`component_session()` 上下文管理器) | 已完成 |
| **Component** | 场景构建器 (`ScenarioBuilder`) | 已完成 |
| **Component** | 卫星构建器 (`SatelliteBuilder`) — 开普勒/笛卡尔/质量/姿态/颜色 | 已完成 |
| **Component** | MCS 构建器 (`McsBuilder`) — 开普勒/笛卡尔/传播/脉冲/目标序列 | 已完成 |
| **Component** | 报告导出 (`ReportExporter`) | 已完成 |

### 测试覆盖

| 测试文件 | 覆盖模块 |
|----------|----------|
| `test_utils.py` | 时间解析、路径操作、CMDRESULT 解析 |
| `connect/test_session.py` | 连接管理、命令发送 |
| `connect/test_scenario.py` | ScenarioBuilder |
| `connect/test_satellite.py` | SatelliteBuilder |
| `connect/test_mcs.py` | McsBuilder |
| `connect/test_facility.py` | FacilityBuilder + SensorBuilder |

Component 模式测试尚未添加（需要 ATK DLL 运行时）。

## 下一版本计划：v0.2.0

### 待实现功能

- [ ] Component 模式测试框架（Mock SWIG 接口）
- [ ] 链 (Chain) 构建 — Connect 模式和 Component 模式
- [ ] 飞机/船/车辆对象支持
- [ ] Connect 模式 `get_object()` / `object_exists()` 方法
- [ ] 传播器高级配置（HPOP 力模型参数等）
- [ ] 报告样式自动发现（从 ATK 安装目录）
- [ ] 异步 Connect 模式支持（asyncio + 非阻塞 TCP）

### 待改进项

- [ ] 星座模式 `run_all()` — 当前串行执行，探索批处理优化
- [ ] 报告解析 — 支持 CSV 格式、自动列检测
- [ ] 错误消息国际化 — 当前混合中英文
- [ ] 日志系统 — 替换 `warnings.warn` 为 `logging`

## 已知限制

1. **Connect 模式不支持并发**：TCP 连接是单工通道，`run_all()` 使用串行执行
2. **SWIG 返回值双重性**：`atkConnect()` 可能返回 `str` 或 `CMDRESULT`，SDK 内部已处理但用户直接调用 `send()` 需注意
3. **TLE 格式严格**：必须提供标准 69 字符 TLE 行
4. **Component 模式平台限制**：仅支持 Windows（依赖 `.pyd` DLL）
5. **CoverageStats 解析脆弱**：依赖 ATK 返回格式，不同版本可能不一致

## 技术决策

| 决策 | 选择 | 原因 |
|------|------|------|
| 构建器模式 | Fluent API (返回 self) | 链式调用、类型安全 |
| 连接管理 | 上下文管理器 | 确保资源释放 |
| 模块注入 | 猴子补丁 `_patch_connection()` | 避免 ATKConnection 导入所有子模块 |
| 类型提示 | `.pyi` 存根文件 | 为猴子补丁方法提供 IDE 支持 |
| 零依赖 | 不引入 pip 依赖 | 减少安装复杂度 |
| Vendored 绑定 | 复制到 `src/vendored/` | 版本隔离、可移植性 |
