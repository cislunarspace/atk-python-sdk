# 代码质量与安全修复计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复代码审查发现的 7 个安全和质量问题，提升代码健壮性。

**Architecture:** 纯修复任务，每个问题独立修复。TLE/坐标校验使用正则验证；CoverageStats 异常时抛出明确错误；format_atk_time 简化逻辑；_patch_connection 通过测试验证；Component mode 补充缺失测试。

**Tech Stack:** Python, pytest, unittest.mock

---

## 文件变更概览

| 文件 | 操作 |
|------|------|
| `src/atk/connect/session.py` | 修改 — ImportError 消息改为 uv |
| `src/atk/connect/satellite.py` | 修改 — TLE 格式校验 |
| `src/atk/connect/facility.py` | 修改 — 坐标范围校验 |
| `src/atk/connect/coverage.py` | 修改 — CoverageStats._parse 错误处理 |
| `src/atk/utils.py` | 修改 — format_atk_time 简化 |
| `src/atk/tests/` | 新增 — Component mode 测试文件 |

---

## Task 1: 更新 ImportError 消息（pip → uv）

**Files:**
- Modify: `src/atk/connect/session.py:33-36`

- [ ] **Step 1: 修改错误消息**

Edit `src/atk/connect/session.py` lines 33-36:

```python
# 现状
raise ImportError(
    "ATKConnectModule not found in src/vendored/. "
    "Ensure the SDK is installed with: pip install -e ."
) from _exc

# 变更为
raise ImportError(
    "ATKConnectModule not found in src/vendored/. "
    "Ensure the SDK is installed with: uv sync"
) from _exc
```

- [ ] **Step 2: 提交**

```bash
git add src/atk/connect/session.py
git commit -m "fix: update ImportError message to use uv instead of pip"
```

---

## Task 2: 添加 TLE 输入校验

**Files:**
- Modify: `src/atk/connect/satellite.py`
- Test: `src/tests/connect/test_satellite.py`

TLE 行必须恰好 69 字符（标准 TLE 格式）。ATK SGP4 传播器依赖此格式，静默畸形的 TLE 会导致 ATK 行为异常。

- [ ] **Step 1: 添加 TLE 校验测试**

在 `src/tests/connect/test_satellite.py` 中添加：

```python
def test_set_state_tle_rejects_invalid_line_length():
    from tests.connect.conftest import MockATKConnection
    from atk.connect.satellite import SatelliteBuilder

    conn = MockATKConnection()
    sat = SatelliteBuilder(conn, "Sat1")

    # Line1 太短
    with pytest.raises(atk_exc.ATKValueError, match="69 characters"):
        sat.set_state_tle(
            line1="1 25544U 98067A   24001.50000000",  # 49 chars
            line2="2 25544  51.6400 208.9163 0006703  44.2800 315.9700 15.49000000400000"
        )

    # Line2 太短
    with pytest.raises(atk_exc.ATKValueError, match="69 characters"):
        sat.set_state_tle(
            line1="1 25544U 98067A   24001.50000000  .00016717  00000-0  10270-3 0  9000",
            line2="2 25544  51.6400 208.9163"  # 32 chars
        )
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest src/tests/connect/test_satellite.py::test_set_state_tle_rejects_invalid_line_length -v`
Expected: FAIL (test exists but validation not implemented yet)

- [ ] **Step 3: 添加 TLE 校验函数**

在 `src/atk/connect/satellite.py` 文件顶部（`_PROPAGATOR_CMD_MAP` 之后）添加：

```python
_TLE_LINE_LENGTH = 69

def _validate_tle_line(line: str, label: str) -> None:
    """校验 TLE 行长度恰好为 69 字符（标准 CCSDS TLE 格式）。"""
    if not isinstance(line, str):
        raise _ex.ATKValueError(f"TLE {label} must be a string, got {type(line).__name__}")
    line = line.strip()
    if len(line) != _TLE_LINE_LENGTH:
        raise _ex.ATKValueError(
            f"TLE {label} must be exactly {_TLE_LINE_LENGTH} characters, "
            f"got {len(line)}: {line!r}"
        )
```

- [ ] **Step 4: 在 set_state_tle 中调用校验**

Edit `src/atk/connect/satellite.py` 的 `set_state_tle` 方法（约第 258 行），在 `self._conn.send` 之前添加：

```python
def set_state_tle(self, line1: str, line2: str) -> "SatelliteBuilder":
    _validate_tle_line(line1, "line1")
    _validate_tle_line(line2, "line2")
    self._conn.send("SetState", self._path, f' TLE "{line1}" "{line2}"')
    ...
```

- [ ] **Step 5: 运行测试验证通过**

Run: `pytest src/tests/connect/test_satellite.py::test_set_state_tle_rejects_invalid_line_length -v`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add src/atk/connect/satellite.py src/tests/connect/test_satellite.py
git commit -m "feat(satellite): add TLE line length validation"
```

---

## Task 3: 添加坐标范围校验

**Files:**
- Modify: `src/atk/connect/facility.py`
- Test: `src/tests/connect/test_facility.py`

- [ ] **Step 1: 添加坐标校验测试**

在 `src/tests/connect/test_facility.py` 中添加：

```python
def test_set_position_rejects_invalid_lat():
    from tests.connect.conftest import MockATKConnection
    from atk.connect.facility import FacilityBuilder

    conn = MockATKConnection()
    facility = FacilityBuilder(conn, "Station1")

    with pytest.raises(atk_exc.ATKValueError, match="latitude.*-90.*90"):
        facility.set_position(lat=95.0, lon=0.0, height=0.0)

def test_set_position_rejects_invalid_lon():
    from tests.connect.conftest import MockATKConnection
    from atk.connect.facility import FacilityBuilder

    conn = MockATKConnection()
    facility = FacilityBuilder(conn, "Station1")

    with pytest.raises(atk_exc.ATKValueError, match="longitude.*-180.*180"):
        facility.set_position(lat=0.0, lon=200.0, height=0.0)
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest src/tests/connect/test_facility.py -k "invalid_lat or invalid_lon" -v`
Expected: FAIL

- [ ] **Step 3: 添加坐标校验逻辑**

Edit `src/atk/connect/facility.py` 的 `set_position` 方法开头（约第 98 行）：

```python
def set_position(self, lat: float, lon: float, height: float = 0.0) -> "FacilityBuilder":
    if not (-90.0 <= lat <= 90.0):
        raise _ex.ATKValueError(
            f"Latitude must be between -90 and 90 degrees, got {lat}"
        )
    if not (-180.0 <= lon <= 180.0):
        raise _ex.ATKValueError(
            f"Longitude must be between -180 and 180 degrees, got {lon}"
        )
    ...
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest src/tests/connect/test_facility.py -k "invalid_lat or invalid_lon" -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/atk/connect/facility.py src/tests/connect/test_facility.py
git commit -m "feat(facility): add latitude/longitude range validation"
```

---

## Task 4: 修复 CoverageStats._parse 静默失败

**Files:**
- Modify: `src/atk/connect/coverage.py`
- Test: `src/tests/connect/test_coverage.py`

当 ATK 返回意外格式时，`CoverageStats` 当前返回 0 值但不报错。应该抛出明确异常。

- [ ] **Step 1: 添加异常情况测试**

在 `src/tests/connect/test_coverage.py` 中添加：

```python
def test_coverage_stats_raises_on_unexpected_format():
    from unittest.mock import MagicMock
    from atk.connect.coverage import CoverageStats

    mock_raw = MagicMock()
    mock_raw.m_vectData = "completely unexpected format without equals signs"

    # 意外格式应该抛出错误而非静默返回 0
    with pytest.raises(atk_exc.ATKError, match="unexpected.*format|failed to parse"):
        stats = CoverageStats(mock_raw)
        _ = stats.access_count  # 触发解析
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest src/tests/connect/test_coverage.py -k "unexpected_format" -v`
Expected: FAIL

- [ ] **Step 3: 修改 _parse 方法**

Edit `src/atk/connect/coverage.py` 的 `_parse` 方法（约第 195 行）：

```python
def _parse(self) -> dict:
    """将原始 CMDRESULT 数据解析为字典。"""
    data = self._data
    if not data:
        return {}
    # 优先尝试 key=value 格式
    result = {}
    positional = []
    for item in data:
        if "=" in item:
            key, val = item.split("=", 1)
            result[key.strip()] = val.strip()
        else:
            positional.append(item)
    # 如果既没有 key=value 也没有足够的 position 数据，抛出异常
    if not result and len(positional) < 3:
        raise _ex.ATKError(
            f"Unexpected CoverageStats format, expected 'key=value' pairs or "
            f"at least 3 positional values, got: {data}"
        )
    # 如果没有 key=value 对，尝试位置解析
    if not result and len(positional) >= 3:
        result["AccessCount"] = positional[0]
        result["TotalAccessTime"] = positional[1]
        result["MeanAccessDuration"] = positional[2] if len(positional) > 2 else "0"
    return result
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest src/tests/connect/test_coverage.py -k "unexpected_format" -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/atk/connect/coverage.py src/tests/connect/test_coverage.py
git commit -m "fix(coverage): raise error on unexpected CoverageStats format"
```

---

## Task 5: 简化 format_atk_time

**Files:**
- Modify: `src/atk/utils.py`
- Test: `src/tests/test_utils.py`

- [ ] **Step 1: 添加 roundtrip 测试**

在 `src/tests/test_utils.py` 的 `TestFormatAtkTime` 类中添加：

```python
def test_format_atk_time_no_leading_zeros():
    from datetime import datetime
    from atk import utils
    # 5 号不应该有前导零
    dt = datetime(2024, 1, 1, 0, 0, 0)
    result = utils.format_atk_time(dt)
    assert result.startswith("1 Jan 2024")  # 日期无前导零
```

- [ ] **Step 2: 运行测试验证**

Run: `pytest src/tests/test_utils.py::TestFormatAtkTime -v`
Expected: PASS（现有实现应该已能通过）

- [ ] **Step 3: 简化 format_atk_time 实现**

Edit `src/atk/utils.py` 的 `format_atk_time` 函数（约第 94 行）：

```python
def format_atk_time(dt: datetime) -> str:
    """
    将 Python ``datetime`` 格式化为 ATK 时间字符串：``"5 Nov 2022 00:00:00.000"``。

    注意：ATK 使用非零填充的日期（如 ``5`` 而非 ``05``）。
    """
    # 构建日期部分：day 是非零填充的月份日期
    date_part = f"{dt.day} {dt:%b %Y}"
    # 时间部分：去掉末尾的 .000 如果为整秒
    time_part = dt.strftime("%H:%M:%S.%f").rstrip("0").rstrip(".")
    return f"{date_part} {time_part}"
```

- [ ] **Step 4: 运行所有 format 测试验证**

Run: `pytest src/tests/test_utils.py::TestFormatAtkTime -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/atk/utils.py src/tests/test_utils.py
git commit -m "refactor(utils): simplify format_atk_time implementation"
```

---

## Task 6: 为 _patch_connection 添加验证测试

**Files:**
- Test: `src/tests/connect/test_session.py`

这个测试验证所有 connect 子模块的猴子补丁在导入后都正确应用到 `ATKConnection`。

- [ ] **Step 1: 添加 patch 验证测试**

在 `src/tests/connect/test_session.py` 末尾添加：

```python
class TestConnectionPatching:
    """验证所有子模块的 monkey patch 正确应用。"""

    def test_all_builder_methods_exist_on_connection(self):
        """验证 create_scenario、create_satellite、mcs_builder、create_facility、create_coverage 都在 ATKConnection 上。"""
        from atk.connect import session
        expected_methods = [
            "create_scenario",
            "create_satellite",
            "mcs_builder",
            "create_facility",
            "create_coverage",
        ]
        for method_name in expected_methods:
            assert hasattr(session.ATKConnection, method_name), \
                f"ATKConnection missing method: {method_name}"
```

- [ ] **Step 2: 运行测试验证通过**

Run: `pytest src/tests/connect/test_session.py::TestConnectionPatching -v`
Expected: PASS（现有实现应该已正确打补丁）

- [ ] **Step 3: 提交**

```bash
git add src/tests/connect/test_session.py
git commit -m "test(session): add monkey-patch verification test"
```

---

## Task 7: 添加 Component mode 测试

**Files:**
- Create: `src/tests/component/__init__.py`
- Create: `src/tests/component/test_session.py`
- Create: `src/tests/component/test_satellite.py`

Component mode 当前完全没有测试。需要覆盖核心功能：ComponentSession、SatelliteBuilder、McsBuilder。

**注意：** Component mode 依赖 ATK DLL，无法在无 ATK 环境下运行真实测试。所有测试使用 `unittest.mock.MagicMock` 模拟 SWIG 对象。

- [ ] **Step 1: 创建 __init__.py**

Create `src/tests/component/__init__.py`:

```python
"""Component mode tests."""
```

- [ ] **Step 2: 添加 ComponentSession 测试**

Create `src/tests/component/test_session.py`:

```python
"""
atk.component.session 的单元测试 — ComponentSession。

使用 unittest.mock 模拟 ATK Component SWIG 对象。
"""

import pytest
from unittest.mock import MagicMock, patch

from atk import exceptions as atk_exc


class TestComponentSessionNewScenario:
    """ComponentSession.new_scenario() 的测试。"""

    def test_new_scenario_returns_scenario_object(self):
        with patch("atk.component.session._ATK") as mock_atk:
            mock_root = MagicMock()
            mock_scenario = MagicMock()
            mock_root.NewScenario.return_value = None
            mock_root.GetCurrentScenario.return_value = mock_scenario
            mock_atk.IAtkObjectRoot.return_value = mock_root

            from atk.component.session import ComponentSession
            session = ComponentSession(mock_root)
            result = session.new_scenario("TestScenario")

            mock_root.NewScenario.assert_called_once_with("TestScenario")
            assert result is mock_scenario
            assert session.scenario is mock_scenario

    def test_new_scenario_raises_if_scenario_already_loaded(self):
        from atk.component.session import ComponentSession

        mock_root = MagicMock()
        session = ComponentSession(mock_root)
        session._scenario = MagicMock()  # 已加载场景

        with pytest.raises(atk_exc.ATKScenarioError, match="already loaded"):
            session.new_scenario("AnotherScenario")


class TestComponentSessionCreateSatellite:
    """ComponentSession.create_satellite() 的测试。"""

    def test_create_satellite_raises_without_scenario(self):
        from atk.component.session import ComponentSession

        mock_root = MagicMock()
        session = ComponentSession(mock_root)
        # 没有加载场景

        with pytest.raises(atk_exc.ATKScenarioError, match="Create a scenario first"):
            session.create_satellite("Sat1")

    def test_create_satellite_calls_new_on_children(self):
        with patch("atk.component.session._ATK") as mock_atk:
            mock_root = MagicMock()
            mock_scenario = MagicMock()
            mock_children = MagicMock()
            mock_sat = MagicMock()
            mock_root.GetCurrentScenario.return_value = mock_scenario
            mock_scenario.GetChildren.return_value = mock_children
            mock_children.New.return_value = mock_sat
            mock_atk.eSatellite = "eSatellite"

            from atk.component.session import ComponentSession
            session = ComponentSession(mock_root)
            session._scenario = mock_scenario

            result = session.create_satellite("Sat1")

            mock_children.New.assert_called_once()
            assert result is mock_sat
```

- [ ] **Step 3: 添加 SatelliteBuilder 测试**

Create `src/tests/component/test_satellite.py`:

```python
"""
atk.component.satellite 的单元测试 — SatelliteBuilder。

使用 unittest.mock 模拟 ISatellite SWIG 对象。
"""

import pytest
from unittest.mock import MagicMock, patch

from atk import exceptions as atk_exc


class TestSatelliteBuilderComponent:
    """Component mode SatelliteBuilder 的测试。"""

    def test_set_keplerian_calls_setstate(self):
        with patch("atk.component.satellite._ATK") as mock_atk:
            mock_atk.ePropagatorTwoBody = "ePropagatorTwoBody"

            from atk.component.satellite import SatelliteBuilder
            mock_sat = MagicMock()
            builder = SatelliteBuilder(mock_sat)

            builder.set_keplerian(sma=6678, ecc=0, inc=28.5, raan=0, argp=0, ta=0)

            mock_sat.SetState.assert_called_once()
            call_args = str(mock_sat.SetState.call_args)
            assert "6678" in call_args
            assert "0" in call_args
            assert "28.5" in call_args

    def test_set_mass_calls_setvalue(self):
        with patch("atk.component.satellite._ATK") as mock_atk:
            from atk.component.satellite import SatelliteBuilder
            mock_sat = MagicMock()
            builder = SatelliteBuilder(mock_sat)

            builder.set_mass(500)

            mock_sat.SetValue.assert_called()
            call_str = str(mock_sat.SetValue.call_args_list)
            assert "TotalMass" in call_str
            assert "500" in call_str
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest src/tests/component/ -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/tests/component/
git commit -m "test(component): add ComponentSession and SatelliteBuilder tests"
```

---

## 实施顺序

1. Task 1: ImportError 消息（最简单的修复）
2. Task 2: TLE 校验
3. Task 3: 坐标范围校验
4. Task 4: CoverageStats._parse 异常
5. Task 5: format_atk_time 简化
6. Task 6: _patch_connection 验证测试
7. Task 7: Component mode 测试（最复杂）

## 验证方式

所有任务完成后：

```bash
pytest src/tests/ -v
```

预期：所有测试通过（包含新增的测试）。
