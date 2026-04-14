"""
ATK Python SDK
==============
Analytical Toolkit (ATK) 的高级 Python 封装。

两种运行模式：

- ``atk.connect`` — Connect 模式：通过 TCP 连接到运行中的 ATK 实例。
  需要 ATK 软件已启动。

- ``atk.component`` — Component 模式：直接加载 DLL，无需 ATK 窗口。
  在 ATK 的嵌入式 Python 环境中运行。

Connect 模式示例::

    from atk.connect import connect

    with connect('127.0.0.1', 6655) as atk:
        atk.new('Scenario', 'MyScenario')
        sat = atk.create_satellite('Sat1')
        sat.set_keplerian(sma=7100, ecc=0.001, inc=30)
        atk.run()

Component 模式示例::

    from atk.component import session

    with session() as root:
        scenario = root.new_scenario('MyScenario')
        sat = scenario.create_satellite('Sat1')
        sat.set_propagator_type('PropagatorAstromaster')
        ...
"""

from atk import exceptions
from atk import utils

__version__ = "0.1.0"

__all__ = [
    "exceptions",
    "utils",
]
