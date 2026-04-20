# 将 Python 包管理器更换为 uv

## 概述

将项目从 setuptools + pip 迁移到 hatchling + uv，统一构建后端和包管理。

## 变更范围

- `pyproject.toml` — 构建系统
- `.github/workflows/ci.yml` — CI 测试流程
- `.github/workflows/release.yml` — 发版流程
- `.github/workflows/docs.yml` — 文档部署流程
- `CLAUDE.md` — 开发者命令参考
- `README.md` — 安装和测试文档
- `docs/guides/getting-started.md` — 快速开始文档

## 1. 构建后端变更

### pyproject.toml

```toml
# build-system
- requires = ["setuptools>=61.0", "wheel"]
- build-backend = "setuptools.build_meta"
+ requires = ["hatchling"]
+ build-backend = "hatchling.build"
```

`[project]` 元数据保持不变（已符合 PEP 621）。`[project.optional-dependencies]` 结构不变。

semantic_release build_command：
```toml
- build_command = "pip install build && python -m build"
+ build_command = "uv build"
```

### hatchling 不需要额外配置

项目结构符合 hatchling 默认（`src/<package>` 布局），`[tool.setuptools.packages.find]` 和 `[tool.setuptools.package-dir]` 可删除，因为 hatchling 通过 `[project]` 的 `requires-python` 和 `dependencies` 自动发现包。

## 2. 文档命令变更

| 文件 | 现状 | 变更后 |
|------|------|--------|
| `CLAUDE.md` | `pip install -e ".[dev]"`, `pip install -e ".[docs]"` | `uv sync --dev`, `uv sync --extra docs` |
| `README.md` | 同上 | 同上 |
| `docs/guides/getting-started.md` | `pip install -e .`, `pip install -e ".[dev]"` | `uv sync`, `uv sync --dev` |

uv 的原则：有 `pyproject.toml` 的项目根目录直接 `uv sync` 即可安装所有依赖（含可选依赖）。无需 `-e .`。

## 3. CI Workflow 变更

### ci.yml

```yaml
# 现状
- uses: actions/setup-python@v5
  with:
    python-version: ${{ matrix.python-version }}
- name: Install dependencies
  run: pip install -e ".[dev]"

# 变更后
- uses: astral-sh/setup-uv@v5
  with:
    enable-cache: true
- name: Install dependencies
  run: uv sync --dev
```

测试命令 `pytest --cov=src --cov-report=term-missing` 不变。

docs job 同理：`pip install -e ".[docs]"` → `uv sync --extra docs`。

### release.yml

```yaml
# 现状
- uses: actions/setup-python@v5
  with:
    python-version: "3.12"
- name: Install semantic-release
  run: pip install python-semantic-release build
- name: Build package
  run: python -m build

# 变更后
- uses: astral-sh/setup-uv@v5
  with:
    enable-cache: true
- name: Run semantic-release
  env:
    GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  run: uvx python-semantic-release version
- name: Build package
  run: uv build
```

`uvx` 是 uv 的临时工具执行器（无需预先安装包），等价于 `pipx run python-semantic-release`。

### docs.yml

```yaml
# 现状
- uses: actions/setup-python@v5
  with:
    python-version: "3.12"
- name: Install dependencies
  run: pip install -e ".[docs]"

# 变更后
- uses: astral-sh/setup-uv@v5
  with:
    enable-cache: true
- name: Install dependencies
  run: uv sync --extra docs
```

## 4. 不受影响的部分

- `src/vendored/` 中的 `.pyd`/`.so` 是预编译二进制，hatchling 不会重新编译它们。
- `semantic_release` 的其他配置（version_toml, changelog_file, upload_to_pypi 等）保持不变。
- Python 版本支持矩阵 `["3.9", "3.10", "3.11", "3.12"]` 保持不变。
- mkdocs 配置 `mkdocs.yml` 不涉及包管理器，不受影响。

## 5. 实施步骤

1. 更新 `pyproject.toml` — 替换构建系统
2. 更新 `CLAUDE.md` — 替换命令
3. 更新 `README.md` — 替换命令
4. 更新 `docs/guides/getting-started.md` — 替换命令
5. 更新 `.github/workflows/ci.yml` — 替换 action 和命令
6. 更新 `.github/workflows/release.yml` — 替换 action 和命令
7. 更新 `.github/workflows/docs.yml` — 替换 action 和命令
8. 提交并推送
