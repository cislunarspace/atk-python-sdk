"""
ATK Connect 模式 — 会话管理

提供 ``ATKConnection``（原始连接）和 ``connect()``（上下文管理器）。
"""

from __future__ import annotations

import time
import warnings
from contextlib import contextmanager
from typing import Any, Generator

from atk import exceptions as _ex
from atk import utils

# ---------------------------------------------------------------------------
# 原始 SWIG 导入 — 来自 vendored/（atk/ 的同级目录，位于 src/ 下）
# ---------------------------------------------------------------------------
import os
import sys

# vendored/ 位于 src/vendored/（atk/ 的同级目录）。相对于此文件解析：
# src/atk/connect/session.py → 向上 3 级 → src/ → vendored/
_vendored_dir = os.path.join(os.path.dirname(__file__), "..", "..", "vendored")
_vendored_dir = os.path.normpath(_vendored_dir)
if _vendored_dir not in sys.path:
    sys.path.insert(0, _vendored_dir)

try:
    import ATKConnectModule as _ATK
except ImportError as _exc:  # pragma: no cover
    raise ImportError(
        "ATKConnectModule not found in src/vendored/. "
        "Ensure the SDK is installed with: pip install -e ."
    ) from _exc


# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 6655
CONNECT_TIMEOUT = 30.0  # 秒
RETRY_ATTEMPTS = 3
RETRY_BACKOFF = 2.0  # 秒


# ---------------------------------------------------------------------------
# ATKConnection — 连接句柄封装
# ---------------------------------------------------------------------------

class ATKConnection:
    """
    ATK Connect 模式 TCP 连接的轻量封装。

    Attributes
    ----------
    con_id : int
        ``atkOpen`` 返回的连接句柄。
    host : str
        远程主机地址。
    port : int
        TCP 端口号。
    is_connected : bool
        连接开启时为 True。
    """

    __slots__ = ("con_id", "host", "port", "_connected")

    def __init__(self, con_id: int, host: str, port: int):
        self.con_id = con_id
        self.host = host
        self.port = port
        self._connected = True

    @property
    def is_connected(self) -> bool:
        return self._connected

    # ------------------------------------------------------------------
    # 核心 ATK 操作
    # ------------------------------------------------------------------

    def send(
        self,
        command: str,
        obj_path: str = "*",
        param: str = "",
    ) -> Any:
        """
        向 ATK 发送 Connect 命令并返回原始结果。

        Parameters
        ----------
        command : str
            Connect 命令名称（如 ``"New"``、``"SetValue"``）。
        obj_path : str
            对象路径（如 ``"*/Satellite/Sat1"``）。对于不针对
            特定对象的命令，使用 ``"*"`` 或 ``""``。
        param : str
            命令的参数字符串。

        Returns
        -------
        str or CMDRESULT
            SWIG DLL 可能返回 ``str``（如 ``"ACK"``/``"NACK"``）
            或 ``CMDRESULT`` 对象。

        Raises
        ------
        ATKConnectionError
            如果连接已关闭。
        ATKCommandError
            如果 ATK 返回错误字符串。
        """
        if not self._connected:
            raise _ex.ATKConnectionError(
                self.host, self.port,
                "Connection is closed"
            )

        # 规范化路径
        obj_path = utils.resolve_path(obj_path)

        # ATK Connect 协议：atkConnect(conID, command, inputStr)
        # 其中 inputStr = "obj_path param"，两者必须合并为一个字符串
        input_str = f"{obj_path} {param}".strip()
        result = _ATK.atkConnect(self.con_id, command, input_str)

        # 打印命令发送和响应，便于调试
        print(f"[ATK] --> {command} {obj_path!r} {param!r}")
        print(f"[ATK] <-- {result!r}")

        # atkConnect() 可能返回 str（如 "NACK"、"ACK"）或 CMDRESULT — 两种都要处理
        if isinstance(result, str):
            raw = result.strip()
            if raw:
                upper = raw.upper().rstrip(":").lstrip("-")
                error_indicators = ("ERROR", "FAIL", "FALSE", "NACK")
                if upper in error_indicators:
                    raise _ex.ATKCommandError(
                        command, obj_path, param, raw_response=raw
                    )
            return result

        # CMDRESULT 路径 — 可能通过 m_vectData 携带错误字符串
        # 直接检查 m_vectData，避免 result_to_list 返回 [] 时漏检错误
        if hasattr(result, "m_vectData"):
            raw = result.m_vectData
            if isinstance(raw, str):
                data = raw.strip().split() if raw.strip() else []
            elif raw:
                data = raw if isinstance(raw, list) else [raw]
            else:
                data = []
            if data:
                upper = data[0].upper().rstrip(":").lstrip("-")
                error_indicators = ("ERROR", "FAIL", "FALSE", "NACK")
                if upper in error_indicators:
                    raise _ex.ATKCommandError(
                        command, obj_path, param,
                        raw_response=" ".join(str(x) for x in data)
                    )
        return result

    def send_str(
        self,
        command: str,
        obj_path: str = "*",
        param: str = "",
    ) -> str:
        """
        类似 ``send()``，但将响应作为普通字符串返回。

        适用于返回单个字符串值的命令（如对象名称、状态消息）。
        """
        result = self.send(command, obj_path, param)
        if isinstance(result, str):
            return result.strip()
        data = utils.result_to_list(result)
        return " ".join(data)

    def close(self) -> None:
        """关闭到 ATK 的 TCP 连接。"""
        if self._connected:
            try:
                _ATK.atkClose(self.con_id)
            finally:
                self._connected = False

    def __repr__(self) -> str:
        status = "open" if self._connected else "closed"
        return f"<ATKConnection {self.host}:{self.port} [{status}]>"


# ---------------------------------------------------------------------------
# 带重试的连接管理器
# ---------------------------------------------------------------------------

class ATKConnectionManager:
    """
    管理 ATK 连接生命周期，失败时自动重试。

    Parameters
    ----------
    host : str
        ATK 服务器主机。默认为 ``"127.0.0.1"``。
    port : int
        ATK 服务器端口。默认为 ``6655``。
    timeout : float
        连接超时（秒）。默认为 ``30``。
    retries : int
        连接失败时的重试次数。默认为 ``3``。
    backoff : float
        重试之间的等待时间（秒）。默认为 ``2.0``。

    示例::

        mgr = ATKConnectionManager('127.0.0.1', 6655, retries=5)
        conn = mgr.connect()
        ...
        conn.close()
    """

    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        timeout: float = CONNECT_TIMEOUT,
        retries: int = RETRY_ATTEMPTS,
        backoff: float = RETRY_BACKOFF,
    ):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.retries = retries
        self.backoff = backoff

    def connect(self) -> ATKConnection:
        """
        打开到 ATK 服务器的连接。

        Raises
        ------
        ATKConnectionError
            所有重试尝试耗尽后抛出。
        """
        last_ex: Exception | None = None

        for attempt in range(1, self.retries + 1):
            try:
                con_id = _ATK.atkOpen(self.host, self.port)
                if con_id is not None and con_id != 0:
                    return ATKConnection(con_id, self.host, self.port)
            except Exception as err:  # pragma: no cover
                last_ex = err

            if attempt < self.retries:
                warnings.warn(
                    f"[{self.host}:{self.port}] Connection attempt {attempt} failed "
                    f"({type(last_ex).__name__}): {last_ex}. "
                    f"Retrying in {self.backoff}s... ({attempt}/{self.retries})",
                    RuntimeWarning,
                )
                time.sleep(self.backoff)

        raise _ex.ATKConnectionError(
            self.host, self.port,
            f"Failed after {self.retries} attempts: {last_ex}"
        )


# ---------------------------------------------------------------------------
# 上下文管理器工厂
# ---------------------------------------------------------------------------

@contextmanager
def connect(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    timeout: float = CONNECT_TIMEOUT,
    retries: int = RETRY_ATTEMPTS,
    backoff: float = RETRY_BACKOFF,
) -> Generator[ATKConnection, None, None]:
    """
    ATK Connect 模式的上下文管理器工厂。

    用法::

        with connect() as atk:
            atk.send('New', '', '/ Scenario MyScenario')

        # 或指定自定义主机/端口：
        with connect('192.168.1.10', 6655) as atk:
            ...

    Yields
    ------
    ATKConnection
    """
    mgr = ATKConnectionManager(host, port, timeout, retries, backoff)
    conn = mgr.connect()
    try:
        yield conn
    finally:
        conn.close()

