"""
ATK Component 模式 SDK
======================
直接 DLL 访问，无需 ATK 软件运行。
通过 ATKComponentPythonModule 使用 ATK 的嵌入式 Python 环境。

用法（在 ATK 的嵌入式 Python 解释器中）::

    from atk.component import session

    with session() as root:
        scenario = root.new_scenario('MyScenario')
        sat = scenario.create_satellite('Sat1')
        sat.set_propagator_type('PropagatorAstromaster')
        ...

注意：Component 模式需要 ATKComponentPythonModule.pyd 和
_ATKComponentPythonModule.pyd DLL 文件。这些文件必须与
ATKComponentPythonModule.py 位于同一目录（通常是 ATK 安装根目录）。
请将这两个文件复制到项目中或将 ATK 安装目录添加到路径。
"""

from atk.component.session import ComponentSession, component_session

__all__ = [
    "ComponentSession",
    "component_session",
]
