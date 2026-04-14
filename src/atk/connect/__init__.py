"""
ATK Connect 模式 SDK
====================
通过 TCP 连接到运行中的 ATK 实例并发送 Connect 命令。

用法::

    from atk.connect import connect

    with connect('127.0.0.1', 6655) as atk:
        atk.new('Scenario', 'MyScenario')
        atk.create_satellite('Sat1')
"""

from atk.connect.session import ATKConnection, ATKConnectionManager
from atk.connect.session import connect

# 导入子模块以触发其 _patch_connection() 调用，这些调用会将
# 工厂方法（create_scenario、create_satellite、constellation_builder、
# create_coverage、mcs_builder）添加到 ATKConnection。
from atk.connect import scenario  # noqa: F401
from atk.connect import satellite  # noqa: F401
from atk.connect import mcs  # noqa: F401
from atk.connect import coverage  # noqa: F401
from atk.connect import constellation  # noqa: F401

__all__ = [
    "ATKConnection",
    "ATKConnectionManager",
    "connect",
]
