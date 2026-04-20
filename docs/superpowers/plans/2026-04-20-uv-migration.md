# uv 迁移实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将项目从 setuptools + pip 迁移到 hatchling + uv，统一构建后端和包管理。

**Architecture:** 替换 pyproject.toml 的 build-system 从 setuptools 改为 hatchling；所有 pip install 命令替换为 uv sync；CI workflow 中的 setup-python action 替换为 setup-uv。

**Tech Stack:** hatchling, uv, astral-sh/setup-uv, python-semantic-release, mkdocs

---

## 文件变更概览

| 文件 | 操作 |
|------|------|
| `pyproject.toml` | 修改 |
| `.github/workflows/ci.yml` | 修改 |
| `.github/workflows/release.yml` | 修改 |
| `.github/workflows/docs.yml` | 修改 |
| `CLAUDE.md` | 修改 |
| `README.md` | 修改 |
| `docs/guides/getting-started.md` | 修改 |

---

## Task 1: 更新 pyproject.toml 构建系统

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: 替换 build-system**

编辑 `pyproject.toml` 第 1-3 行：

```toml
# 现状
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

# 变更为
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

- [ ] **Step 2: 删除 setuptools 相关配置**

删除 `[tool.setuptools.packages.find]` 和 `[tool.setuptools.package-dir]` 两个 section（第 41-47 行）。hatchling 通过 PEP 621 的 `[project]` 元数据自动发现包，无需这些配置。

- [ ] **Step 3: 更新 semantic_release build_command**

编辑 `pyproject.toml` 第 53 行：

```toml
# 现状
build_command = "pip install build && python -m build"

# 变更为
build_command = "uv build"
```

- [ ] **Step 4: 提交**

```bash
git add pyproject.toml
git commit -m "refactor: migrate from setuptools to hatchling build backend"
```

---

## Task 2: 更新 CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: 替换安装命令**

编辑 `CLAUDE.md` 第 7-14 行，将所有 `pip install` 替换为 `uv sync`：

```bash
# 现状
pip install -e ".[dev]"              # install with dev dependencies
python -m pytest src/tests/ -v       # run all tests
python -m pytest src/tests/test_utils.py -v                          # single file
python -m pytest src/tests/test_utils.py::TestParseAtkTime::test_full_datetime -v  # single test
python -m pytest src/tests/ -v --cov=src --cov-report=term-missing  # with coverage
pip install -e ".[docs]" && mkdocs serve  # build docs locally

# 变更为
uv sync --dev              # install with dev dependencies
python -m pytest src/tests/ -v       # run all tests
python -m pytest src/tests/test_utils.py -v                          # single file
python -m pytest src/tests/test_utils.py::TestParseAtkTime::test_full_datetime -v  # single test
python -m pytest src/tests/ -v --cov=src --cov-report=term-missing  # with coverage
uv sync --extra docs && mkdocs serve  # build docs locally
```

注意：pytest 命令不变（只是安装依赖的命令变了）。

- [ ] **Step 2: 提交**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md pip commands to uv"
```

---

## Task 3: 更新 README.md

**Files:**
- Modify: `README.md`

- [ ] **Step 1: 替换安装命令（第 21-26 行）**

```bash
# 现状
## Installation

```bash
pip install -e .
```
...

```python
from atk.connect import connect           # Connect mode
from atk.component import component_session  # Component mode
```

# 变更为
## Installation

```bash
uv sync
```
...

```python
from atk.connect import connect           # Connect mode
from atk.component import component_session  # Component mode
```

```

- [ ] **Step 2: 替换构建文档命令（第 166-169 行）**

```bash
# 现状
```bash
pip install -e ".[docs]"
mkdocs serve
```

# 变更为
```bash
uv sync --extra docs
mkdocs serve
```

```

- [ ] **Step 3: 替换测试命令（第 172-176 行）**

```bash
# 现状
```bash
pip install -e ".[dev]"
python -m pytest src/tests/ -v
```

# 变更为
```bash
uv sync --dev
python -m pytest src/tests/ -v
```

```

- [ ] **Step 4: 提交**

```bash
git add README.md
git commit -m "docs: update README.md pip commands to uv"
```

---

## Task 4: 更新 docs/guides/getting-started.md

**Files:**
- Modify: `docs/guides/getting-started.md`

- [ ] **Step 1: 替换安装命令（第 1-19 行）**

```bash
# 现状
### 基本安装

```bash
pip install -e .
```

### 开发安装

```bash
pip install -e ".[dev]"
```

# 变更为
### 基本安装

```bash
uv sync
```

### 开发安装

```bash
uv sync --dev
```

```

- [ ] **Step 2: 提交**

```bash
git add docs/guides/getting-started.md
git commit -m "docs: update getting-started.md pip commands to uv"
```

---

## Task 5: 更新 CI Workflow（ci.yml）

**Files:**
- Modify: `.github/workflows/ci.yml`

- [ ] **Step 1: 替换 test job 的 setup 和安装命令**

编辑 `.github/workflows/ci.yml` 第 19-28 行：

```yaml
# 现状
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: pip install -e ".[dev]"

      - name: Run tests
        run: pytest --cov=src --cov-report=term-missing

# 变更为
      - name: Set up Python ${{ matrix.python-version }}
        uses: astral-sh/setup-uv@v5
        with:
          enable-cache: true

      - name: Install dependencies
        run: uv sync --dev

      - name: Run tests
        run: pytest --cov=src --cov-report=term-missing
```

- [ ] **Step 2: 替换 docs job 的 setup 和安装命令**

编辑 `.github/workflows/ci.yml` 第 36-44 行：

```yaml
# 现状
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install docs dependencies
        run: pip install -e ".[docs]"

      - name: Build docs
        run: mkdocs build

# 变更为
      - name: Set up Python
        uses: astral-sh/setup-uv@v5
        with:
          enable-cache: true

      - name: Install docs dependencies
        run: uv sync --extra docs

      - name: Build docs
        run: mkdocs build
```

- [ ] **Step 3: 提交**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: migrate ci.yml from setup-python/pip to setup-uv"
```

---

## Task 6: 更新 Release Workflow（release.yml）

**Files:**
- Modify: `.github/workflows/release.yml`

- [ ] **Step 1: 替换 setup 和安装命令**

编辑 `.github/workflows/release.yml` 第 21-36 行：

```yaml
# 现状
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install semantic-release
        run: pip install python-semantic-release build

      - name: Run semantic-release
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          semantic-release version

      - name: Build package
        run: python -m build

# 变更为
      - name: Set up Python
        uses: astral-sh/setup-uv@v5
        with:
          enable-cache: true

      - name: Run semantic-release
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: uvx python-semantic-release version

      - name: Build package
        run: uv build
```

注意：`uvx python-semantic-release` 等价于 `pip install python-semantic-release && semantic-release`，uvx 是 uv 的临时工具执行器。

- [ ] **Step 2: 提交**

```bash
git add .github/workflows/release.yml
git commit -m "ci: migrate release.yml from setup-python/pip to setup-uv"
```

---

## Task 7: 更新 Docs Workflow（docs.yml）

**Files:**
- Modify: `.github/workflows/docs.yml`

- [ ] **Step 1: 替换 setup 和安装命令**

编辑 `.github/workflows/docs.yml` 第 16-25 行：

```yaml
# 现状
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: pip install -e ".[docs]"

      - name: Deploy to GitHub Pages
        run: mkdocs gh-deploy --force

# 变更为
      - name: Set up Python
        uses: astral-sh/setup-uv@v5
        with:
          enable-cache: true

      - name: Install dependencies
        run: uv sync --extra docs

      - name: Deploy to GitHub Pages
        run: mkdocs gh-deploy --force
```

- [ ] **Step 2: 提交**

```bash
git add .github/workflows/docs.yml
git commit -m "ci: migrate docs.yml from setup-python/pip to setup-uv"
```

---

## Task 8: 最终验证

- [ ] **Step 1: 确认所有文件已修改**

运行以下命令确认所有 pip 相关命令已替换：

```bash
grep -rn "pip install" . --include="*.yml" --include="*.md" --include="pyproject.toml" || echo "No pip install found"
grep -rn "setup-python" . --include="*.yml" || echo "No setup-python found"
grep -rn "setuptools" pyproject.toml || echo "No setuptools found"
```

期望输出：`No pip install found`、`No setup-python found`、`No setuptools found`。

- [ ] **Step 2: 推送到远程**

```bash
git push origin master
```

---

## 实施顺序

1. Task 1: pyproject.toml（构建后端是其他一切的基础）
2. Task 2: CLAUDE.md
3. Task 3: README.md
4. Task 4: getting-started.md
5. Task 5: ci.yml
6. Task 6: release.yml
7. Task 7: docs.yml
8. Task 8: 最终验证

## 验证方式

CI pipeline 本身验证变更正确性：
- `uv sync --dev` 成功安装依赖
- `uv build` 成功构建分发包
- `pytest` 测试通过
- `mkdocs build` 文档构建成功
