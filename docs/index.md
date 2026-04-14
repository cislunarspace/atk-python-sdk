# ATK Python SDK 文档

## 项目定位

**ATK Python SDK** 是第三方创建的 ATK Python 二次开发库，基于 ATK 官方 Connect 协议和 Component 接口封装，提供更高层次的 Python API。

本库是对 [ATK 官方 Python 客户端](https://www.osredm.com/atknudt/atk/about) 的补充和完善：

- **官方定位**：ATK 官方提供的 Python 客户端支持 Connect 命令和 Python 语法混合解析
- **本库定位**：提供构建器模式、异常体系、轨道力学工具等高级特性，简化常见操作

> ATK (Aerospace Tool Kit) 是中国国防科技大学自主研发的航天任务分析与设计软件，可替代 STK，已在 300 余家单位部署应用。
> 官方网站：https://www.osredm.com/atknudt/atk/about

## 层级关系

```
用户代码
    │
    ├── ATK Python SDK（本库）        # 高层次封装
    │       │
    │       ├── Connect 模式 ──────► ATK 软件（运行中）  # TCP 连接
    │       │
    │       └── Component 模式 ────► ATK DLL              # 直接加载
    │
    └── ATK 官方 Python 客户端        # 官方接口
```

SDK 提供两种运行模式：

| 模式 | 需要 ATK 图形界面 | 实现方式 | 适用场景 |
|------|-----------------|----------|----------|
| **Connect 模式** | 是（必须运行） | TCP 连接 + Connect 命令字符串 | 客户端连接远程 ATK、脚本控制 |
| **Component 模式** | 否 | 直接加载 ATK 原生 DLL | 自动化测试、嵌入式部署、无图形界面环境 |

## 核心特性

- **双模式架构**：Connect 和 Component 模式共享相同的上层 API 设计
- **构建器模式**：使用流畅的 Python API 构建卫星、场景、MCS 机动序列
- **轨道力学支持**：内置开普勒根数、笛卡尔坐标、时间格式解析
- **异常体系**：完整的异常层次结构，便于精确错误处理

## 文档结构

```
docs/
├── 架构/                    # 两种模式的内部架构
│   ├── connect-mode.md      # Connect 模式原理
│   ├── component-mode.md    # Component 模式原理
│   └── design-decisions.md  # 设计决策及理由
│
├── 背景知识/                # ATK 底层知识
│   ├── atk-object-model.md  # ATK 对象模型和路径约定
│   ├── time-and-units.md   # 时间格式和单位
│   └── vendored-modules.md # Vendored 模块说明
│
├── 指南/                    # 使用教程
│   ├── getting-started.md   # 快速开始
│   ├── orbital-mechanics-primer.md  # 轨道力学基础
│   └── troubleshooting.md  # 常见问题排查
│
└── 参考/
    └── atk-commands.md      # ATK Connect 命令参考
```

## 快速链接

- [快速开始](./guides/getting-started.md) — 5 分钟上手
- [Connect 模式](./architecture/connect-mode.md) — TCP 连接和命令发送
- [Component 模式](./architecture/component-mode.md) — DLL 直接加载
- [轨道力学基础](./guides/orbital-mechanics-primer.md) — 理解示例代码中的公式

## 支持

如遇到问题，请参考[故障排查指南](./guides/troubleshooting.md)。
