"""
ATK Component 模式 — 会话管理

提供 ``ComponentSession``（IAtkObjectRoot 封装）和
``component_session()`` 上下文管理器。
"""

from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from typing import Any, Generator

from atk import exceptions as _ex

# ---------------------------------------------------------------------------
# 定位 ATK Component Python 模块
# ---------------------------------------------------------------------------

# ATK Component DLL + Python 封装位于 ATK 安装目录中。
# 默认情况下，我们在此文件的同级目录中查找 _ATKComponentPythonModule.pyd，
# 或在 ATK 安装目录中查找。用户也可以设置 ATK_ROOT 环境变量。

_ATK_ROOT_ENV = os.environ.get("ATK_ROOT", "")

def _find_component_module() -> Any:
    """
    定位并导入 ATKComponentPythonModule。

    策略：
    1. 如果已可导入，直接使用。
    2. 尝试此文件的同级目录（项目本地副本）。
    3. 尝试环境变量 ATK_ROOT。
    4. 添加到 sys.path 后重试。
    """
    try:
        import ATKComponentPythonModule as m
        return m
    except ImportError:
        pass

    candidates = [
        os.path.join(os.path.dirname(__file__), "..", "..", "vendored"),  # 仓库根目录的 vendored/
        os.path.join(os.path.dirname(__file__), "..", ".."),             # 仓库根目录
        os.path.join(_ATK_ROOT_ENV),                                     # ATK 安装目录
    ]

    for candidate in candidates:
        module_init = os.path.join(candidate, "ATKComponentPythonModule.py")
        if os.path.exists(module_init):
            if candidate not in sys.path:
                sys.path.insert(0, candidate)
            try:
                import ATKComponentPythonModule as m
                return m
            except ImportError:
                pass

    raise _ex.ATKComponentError(
        "ATKComponentPythonModule not found. "
        "Copy ATKComponentPythonModule.py and _ATKComponentPythonModule.pyd "
        "to this project directory, or set ATK_ROOT environment variable."
    )


# ---------------------------------------------------------------------------
# 导入模块（可能抛出上方的 ATKComponentError）
# ---------------------------------------------------------------------------
_ATK = _find_component_module()


# ---------------------------------------------------------------------------
# 传播器类型枚举值（来自 SWIG 封装）
# ---------------------------------------------------------------------------
_PROPAGATOR_NAMES = {
    "PropagatorTwoBody":        getattr(_ATK, "ePropagatorTwoBody", None),
    "PropagatorJ2Perturbation": getattr(_ATK, "ePropagatorJ2Perturbation", None),
    "PropagatorHPOP":          getattr(_ATK, "ePropagatorHPOP", None),
    "PropagatorSGP4":          getattr(_ATK, "ePropagatorSGP4", None),
    "PropagatorStkExternal":   getattr(_ATK, "ePropagatorStkExternal", None),
    "PropagatorAstromaster":   getattr(_ATK, "ePropagatorAstromaster", None),
    "PropagatorGreatArc":      getattr(_ATK, "ePropagatorGreatArc", None),
    "PropagatorSimpleAscent":   getattr(_ATK, "ePropagatorSimpleAscent", None),
    "PropagatorJ4Perturbation": getattr(_ATK, "ePropagatorJ4Perturbation", None),
    "PropagatorVinti":         getattr(_ATK, "ePropagatorVinti", None),
    "PropagatorBallistic":     getattr(_ATK, "ePropagatorBallistic", None),
}


def _resolve_propagator_type(name_or_enum: Any) -> Any:
    """将传播器名称字符串转换为 SWIG 枚举值。"""
    if isinstance(name_or_enum, str):
        enum = _PROPAGATOR_NAMES.get(name_or_enum)
        if enum is None:
            raise _ex.ATKValueError(
                f"Unknown propagator type {name_or_enum!r}. "
                f"Valid names: {list(k for k in _PROPAGATOR_NAMES if _PROPAGATOR_NAMES[k])}"
            )
        return enum
    return name_or_enum


# ---------------------------------------------------------------------------
# ComponentSession — IAtkObjectRoot 封装
# ---------------------------------------------------------------------------

class ComponentSession:
    """
    ATK Component 模式下 ``IAtkObjectRoot`` 的高级封装。

    Attributes
    ----------
    root : IAtkObjectRoot
        底层 SWIG 封装对象。
    scenario : IScenario 或 None
        当前加载的场景（由 :meth:`load_scenario` 或
        :meth:`new_scenario` 设置）。

    示例::

        with component_session() as session:
            session.new_scenario('MyScenario')
            sat = session.create_satellite('Sat1')
            ...
    """

    __slots__ = ("root", "_scenario")

    def __init__(self, root: Any):
        self.root = root
        self._scenario: Any = None

    # ------------------------------------------------------------------
    # 场景生命周期
    # ------------------------------------------------------------------

    def new_scenario(self, name: str) -> Any:
        """
        创建新场景。

        Parameters
        ----------
        name : str
            场景名称。

        Returns
        -------
        IScenario
            新创建的场景对象。

        Raises
        ------
        ATKScenarioError
            如果场景已存在。
        """
        if self._scenario is not None:
            raise _ex.ATKScenarioError(
                "A scenario is already loaded. Close it first with close_scenario()."
            )
        self.root.NewScenario(name)
        self._scenario = self.root.GetCurrentScenario()
        return self._scenario

    def load_scenario(self, path: str) -> Any:
        """
        从 XML 文件加载已有场景。

        Parameters
        ----------
        path : str
            绝对或 ATK 相对场景路径
            （如 ``"C:/ATK/Scenarios/Scenario1.xml"``）。

        Returns
        -------
        IScenario
        """
        if self._scenario is not None:
            raise _ex.ATKScenarioError(
                "A scenario is already loaded. Close it first."
            )
        self.root.LoadScenario(path)
        self._scenario = self.root.GetCurrentScenario()
        return self._scenario

    def close_scenario(self) -> None:
        """关闭当前场景（不保存）。"""
        if self._scenario is not None:
            self.root.CloseScenario()
            self._scenario = None

    def save_scenario(self, path: str | None = None) -> None:
        """
        保存当前场景。

        Parameters
        ----------
        path : str, optional
            保存路径。如果省略，保存到场景当前路径
            （如果是新场景，ATK 会提示选择路径）。
        """
        if self._scenario is None:
            raise _ex.ATKScenarioError("No scenario is currently loaded.")
        if path:
            self.root.SaveScenario(path)
        else:
            self.root.SaveScenario()

    @property
    def scenario(self) -> Any:
        """返回当前加载的场景（或 None）。"""
        return self._scenario

    @property
    def is_open(self) -> bool:
        return self._scenario is not None

    # ------------------------------------------------------------------
    # 对象创建辅助方法
    # ------------------------------------------------------------------

    def create_satellite(self, name: str) -> Any:
        """
        在当前场景中创建新卫星。

        需要先加载场景。

        Returns
        -------
        ISatellite 封装（参见 ``atk.component.satellite`` 获取更高级的类）。
        """
        if self._scenario is None:
            raise _ex.ATKScenarioError("Create a scenario first with new_scenario() or load_scenario().")
        children = self._scenario.GetChildren()
        sat = children.New(_ATK.eSatellite, name)
        return sat

    def get_object(self, path: str) -> Any:
        """
        通过 ATK 路径检索对象（如 ``"Satellite/Sat1"``）。

        Returns
        -------
        IAtkObject（由调用方转换为适当类型）。
        """
        obj = self.root.GetObjectFromPath(path)
        if obj is None:
            raise _ex.ATKObjectNotFoundError(path)
        return obj

    def object_exists(self, path: str) -> bool:
        """检查指定路径是否存在对象。"""
        return self.root.ObjectExists(path)

    # ------------------------------------------------------------------
    # 动画控制
    # ------------------------------------------------------------------

    def play(self) -> None:
        """正向播放当前场景的动画。"""
        self.root.GetAnimation().PlayForward()

    def reset(self) -> None:
        """将动画重置到开始时间。"""
        self.root.GetAnimation().Reset()

    # ------------------------------------------------------------------
    # 报告导出
    # ------------------------------------------------------------------

    def output_report(
        self,
        obj: Any,
        report_type: str,
        start: str,
        stop: str,
        output_path: str | None = None,
    ) -> str:
        """
        生成数据报告并可选地保存到文件。

        Parameters
        ----------
        obj : IAtkObject
            要生成报告的对象（如 ISatellite）。
        report_type : str
            报告样式名称（如 ``"J2000 Position Velocity"``）。
        start : str
            开始时间字符串（ATK 格式，如 ``"5 Nov 2022 00:00:00.000"``）。
        stop : str
            结束时间字符串。
        output_path : str, optional
            输出文件路径。如果为 None，返回默认输出路径。

        Returns
        -------
        str
            生成的报告文件路径。
        """
        if output_path:
            # ATK 的 OutputDataReport 返回路径字符串
            return self.root.OutputDataReport(obj, report_type, start, stop, output_path)
        return self.root.OutputDataReport(obj, report_type, start, stop)

    def __repr__(self) -> str:
        scen = self._scenario.GetInstanceName() if self._scenario else "no scenario"
        return f"<ComponentSession scenario={scen!r}>"


# ---------------------------------------------------------------------------
# 上下文管理器工厂
# ---------------------------------------------------------------------------

@contextmanager
def component_session() -> Generator[ComponentSession, None, None]:
    """
    创建和销毁 ATK Component 会话的上下文管理器。

    用法::

        with component_session() as session:
            session.new_scenario('MyScenario')
            ...

    Yields
    ------
    ComponentSession
    """
    root = _ATK.IAtkObjectRoot()
    session = ComponentSession(root)
    try:
        yield session
    finally:
        if session._scenario is not None:
            session.root.CloseScenario()


__all__ = [
    "ComponentSession",
    "component_session",
]
