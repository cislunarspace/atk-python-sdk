"""
Connect 模式测试共享的 MockATKConnection fixture。
"""

import pytest
from unittest.mock import MagicMock


class MockATKConnection:
    """最小 ATKConnection 模拟，用于 Connect 模式单元测试。"""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str]] = []
        self._connected = True

    def send(self, command: str, obj_path: str = "*", param: str = "") -> MagicMock:
        self.calls.append((command, obj_path, param))
        result = MagicMock()
        result.m_vectData = "OK"
        return result

    @property
    def is_connected(self) -> bool:
        return self._connected


@pytest.fixture
def mock_conn() -> MockATKConnection:
    return MockATKConnection()
