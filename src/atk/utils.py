"""
ATK Python SDK 共享工具函数。
"""

from __future__ import annotations

import re
import warnings
from datetime import datetime
from typing import Callable

from atk.exceptions import ATKValueError

# ----------------------------------------------------------------------
# 时间字符串解析
# ----------------------------------------------------------------------

# ATK 文档和 Connect 命令响应中观察到的时间格式。
# 示例："5 Nov 2022 00:00:00.000"、"5 Nov 2022"、"Jan 2000"
_ATK_TIME_FORMATS = [
    "%d %b %Y %H:%M:%S.%f",
    "%d %b %Y %H:%M:%S",
    "%d %b %Y",
    "%b %Y",
]

_R_DATE_STRICT = re.compile(
    r'^(\d{1,2})\s+(\w+)\s+(\d{4})\s+(\d{1,2}:\d{2}:\d{2}(?:\.\d+)?)$'
)
_R_DATE_SHORT = re.compile(r'^(\d{1,2})\s+(\w+)\s+(\d{4})$')
_R_DATETIME_COMPACT = re.compile(
    r'^(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2}):(\d{2})(?:\.\d+)?$'
)

# 月份名称到数字的映射
_MONTH_MAP = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "may": 5, "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def parse_atk_time(time_str: str) -> datetime:
    """
    将 ATK 时间字符串解析为 Python ``datetime``。

    支持的格式（均假设为 UTC）：
    - ``"5 Nov 2022 00:00:00.000"``
    - ``"5 Nov 2022"``
    - ``"5 Nov 2022 00:00:00"``

    无法解析时抛出 ``ATKValueError``。
    """
    s = time_str.strip()
    if not s:
        raise ATKValueError(f"Empty time string")

    # 优先尝试紧凑的 ISO 类格式
    m = _R_DATETIME_COMPACT.match(s)
    if m:
        year, month, day, hour, minute, sec = m.groups()
        return datetime(int(year), int(month), int(day),
                        int(hour), int(minute), int(float(sec)))

    # 尝试 "5 Nov 2022 HH:MM:SS.mmm"
    m = _R_DATE_STRICT.match(s)
    if m:
        day, mon_str, year, hms = m.groups()
        mon = _MONTH_MAP.get(mon_str.lower())
        if mon is None:
            raise ATKValueError(f"Unknown month: {mon_str}")
        parts = hms.split(":")
        hour, minute = int(parts[0]), int(parts[1])
        sec = float(parts[2])
        return datetime(int(year), mon, int(day), hour, minute, int(sec), int((sec % 1) * 1e6))

    # 尝试 "5 Nov 2022"
    m = _R_DATE_SHORT.match(s)
    if m:
        day, mon_str, year = m.groups()
        mon = _MONTH_MAP.get(mon_str.lower())
        if mon is None:
            raise ATKValueError(f"Unknown month: {mon_str}")
        return datetime(int(year), mon, int(day))

    # 回退：让 datetime 尝试各种格式
    for fmt in _ATK_TIME_FORMATS:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass

    raise ATKValueError(f"Unrecognized time format: {time_str!r}")


def format_atk_time(dt: datetime) -> str:
    """
    将 Python ``datetime`` 格式化为 ATK 时间字符串：``"5 Nov 2022 00:00:00.000"``。

    注意：ATK 使用非零填充的日期（如 ``5`` 而非 ``05``）。
    """
    # %-d 在 Windows 上不支持，所以先格式化再手动去前导零
    date_part = dt.strftime("%d %b %Y")
    day = str(dt.day)  # 非零填充
    date_part = f"{day} {dt.strftime('%b %Y')}"
    time_part = dt.strftime("%H:%M:%S.%f").rstrip("0").rstrip(".")
    return f"{date_part} {time_part}"


# ----------------------------------------------------------------------
# 路径工具
# ----------------------------------------------------------------------

def resolve_path(path: str, default_root: str = "*") -> str:
    """
    确保路径以 ``*``（场景根通配符）开头。

    >>> resolve_path("*/Satellite/Sat1")
    '*/Satellite/Sat1'
    >>> resolve_path("Satellite/Sat1")
    '*/Satellite/Sat1'
    >>> resolve_path("/Satellite/Sat1")
    '*/Satellite/Sat1'
    """
    path = path.strip()
    if not path.startswith("*"):
        if path.startswith("/"):
            return f"*{path}"
        return f"*/{path}"
    return path


def path_join(*parts: str) -> str:
    """
    拼接 ATK 对象路径组件。

    >>> path_join("*", "Satellite", "Sat1")
    '*/Satellite/Sat1'
    >>> path_join("*/Scenario/Sc1", "Satellite", "Sat1")
    '*/Scenario/Sc1/Satellite/Sat1'
    """
    joined = "/".join(parts)
    # 规范化：合并双斜杠
    while "//" in joined:
        joined = joined.replace("//", "/")
    # 确保路径以 */ 开头
    if not joined.startswith("*"):
        joined = "*/" + joined.lstrip("/")
    return joined


def path_parent(path: str) -> str:
    """返回父路径（最后一个斜杠之前的所有内容）。"""
    if "/" not in path:
        return "*"
    return "/".join(path.rsplit("/", 1)[:-1]) or "*"


def path_name(path: str) -> str:
    """返回路径的最后一个组件（对象名称）。"""
    return path.rsplit("/", 1)[-1]


# ----------------------------------------------------------------------
# CMDRESULT 解析辅助函数
# ----------------------------------------------------------------------

def result_to_list(result) -> list[str]:
    """
    将 ``CMDRESULT`` SWIG 封装或原始字符串转换为字符串列表。

    SWIG DLL 的 ``atkConnect()`` 可能返回 ``str``（如 ``"ACK"``/``"NACK"``）
    或 ``CMDRESULT`` 对象——此函数处理两种情况。
    """
    if result is None:
        return []
    if isinstance(result, str):
        stripped = result.strip()
        return stripped.split() if stripped else []
    if hasattr(result, "m_vectData") and result.m_vectData:
        # m_vectData 可能是字符串或已经是列表
        data = result.m_vectData
        if isinstance(data, str):
            return data.split()
        return list(data)
    return []


def result_to_dict(result, keys: list[str]) -> dict[str, str]:
    """
    使用 ``keys`` 作为列名，将 ``CMDRESULT`` 转换为 ``dict``。

    结果长度与键长度不匹配时抛出 ``ATKValueError``。
    """
    values = result_to_list(result)
    if len(values) != len(keys):
        raise ATKValueError(
            f"Result has {len(values)} values but expected {len(keys)}: {values}"
        )
    return dict(zip(keys, values))


# ----------------------------------------------------------------------
# 验证辅助函数
# ----------------------------------------------------------------------

def validate_name(name: str) -> str:
    """
    验证并清理 ATK 对象名称。

    对象名称必须非空，最长 64 个字符，且不包含
    ATK 路径中的特殊字符（``/``、``*``、``:``）。
    """
    if not name or not name.strip():
        raise ATKValueError("Object name must be non-empty")
    if len(name) > 64:
        raise ATKValueError(f"Object name exceeds 64 characters: {name!r}")
    invalid = set("/*:")
    bad = invalid.intersection(name)
    if bad:
        raise ATKValueError(f"Object name contains invalid characters {bad}: {name!r}")
    return name.strip()
