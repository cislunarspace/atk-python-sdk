"""
ATK SDK 自定义异常层级。
"""

from __future__ import annotations


class ATKError(Exception):
    """所有 ATK SDK 错误的基类异常。"""

    pass


class ATKConnectionError(ATKError):
    """连接 ATK 失败时抛出（Connect 模式）。"""

    def __init__(self, host: str, port: int, message: str | None = None):
        self.host = host
        self.port = port
        detail = message or "Could not establish connection"
        super().__init__(f"[{host}:{port}] {detail}")


class ATKConnectionTimeout(ATKConnectionError):
    """连接 ATK 超时时抛出。"""

    def __init__(self, host: str, port: int, timeout: float):
        self.timeout = timeout
        super().__init__(host, port, f"Connection timed out after {timeout}s")


class ATKObjectNotFoundError(ATKError):
    """基于路径的对象查找失败时抛出。"""

    def __init__(self, path: str):
        self.path = path
        super().__init__(f"ATK object not found: {path}")


class ATKCommandError(ATKError):
    """ATK Connect 命令返回错误时抛出。"""

    def __init__(self, command: str, path: str, param: str, raw_response: str = ""):
        self.command = command
        self.path = path
        self.param = param
        self.raw_response = raw_response
        msg = f"Command '{command}' failed for '{path}'"
        if param:
            msg += f" with params: {param}"
        if raw_response:
            msg += f" — {raw_response}"
        super().__init__(msg)


class ATKScenarioError(ATKError):
    """场景级别错误时抛出（加载、保存、创建）。"""

    pass


class ATKSatelliteError(ATKError):
    """卫星配置或传播错误时抛出。"""

    pass


class ATKMCSError(ATKError):
    """MCS（任务控制序列）构建或运行错误时抛出。"""

    pass


class ATKReportError(ATKError):
    """报告生成或解析失败时抛出。"""

    pass


class ATKComponentError(ATKError):
    """Component 模式 DLL 加载或初始化错误时抛出。"""

    pass


class ATKValueError(ATKError, ValueError):
    """提供的值无效时抛出（如错误的时间字符串、错误的轨道元素）。"""

    pass
