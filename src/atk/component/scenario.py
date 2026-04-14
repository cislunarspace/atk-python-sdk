"""
ATK Component 模式 — 场景构建器

用 Python 风格的流式 API 封装 ``IScenario``。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from atk.component.session import ComponentSession


class ScenarioBuilder:
    """
    ATK Component 模式下 ``IScenario`` 的 Python 风格封装。

    通过 :meth:`ComponentSession.new_scenario()` 或
    :meth:`ComponentSession.load_scenario()` 创建。

    示例::

        with component_session() as session:
            scenario = session.new_scenario('MyMission')
            scenario.set_analysis_period('1 Jan 2024', '7 Jan 2024')
            sat = scenario.create_satellite('Sat1')
            ...
    """

    def __init__(self, session: "ComponentSession", scenario_obj: Any):
        self._session = session
        self._scenario = scenario_obj

    # ------------------------------------------------------------------
    # 属性
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        """返回场景的实例名称。"""
        return self._scenario.GetInstanceName()

    @property
    def path(self) -> str:
        """返回场景的完整 ATK 路径。"""
        return self._scenario.GetPath()

    @property
    def scenario(self) -> Any:
        """返回原始 ``IScenario`` SWIG 对象。"""
        return self._scenario

    # ------------------------------------------------------------------
    # 时间配置
    # ------------------------------------------------------------------

    def set_analysis_period(self, start: str, stop: str) -> "ScenarioBuilder":
        """
        设置分析时间段。

        Parameters
        ----------
        start : str
            开始时间字符串（如 ``"5 Nov 2022 00:00:00.000"``）。
        stop : str
            结束时间字符串。
        """
        self._scenario.SetTimePeriod(start, stop)
        return self

    def set_start_time(self, start: str) -> "ScenarioBuilder":
        """设置场景开始时间。"""
        self._scenario.SetStartTime(start)
        return self

    def set_stop_time(self, stop: str) -> "ScenarioBuilder":
        """设置场景结束时间。"""
        self._scenario.SetStopTime(stop)
        return self

    def get_start_time(self) -> str:
        """返回场景开始时间字符串。"""
        return self._scenario.GetStartTime()

    def get_stop_time(self) -> str:
        """返回场景结束时间字符串。"""
        return self._scenario.GetStopTime()

    # ------------------------------------------------------------------
    # 场景生命周期
    # ------------------------------------------------------------------

    def save(self, path: str | None = None) -> "ScenarioBuilder":
        """
        保存场景。

        Parameters
        ----------
        path : str, optional
            保存路径。如果省略，保存到场景当前路径。
        """
        if path:
            self._session.root.SaveScenario(path)
        else:
            self._session.root.SaveScenario()
        return self

    def close(self) -> None:
        """关闭此场景。"""
        self._session.root.CloseScenario()

    # ------------------------------------------------------------------
    # 对象创建
    # ------------------------------------------------------------------

    def create_satellite(self, name: str) -> Any:
        """
        在此场景中创建新卫星。

        Parameters
        ----------
        name : str
            卫星名称。

        Returns
        -------
        ISatellite
            原始 SWIG 卫星对象。
            参见 :mod:`atk.component.satellite` 获取更高级的封装。
        """
        children = self._scenario.GetChildren()
        sat = children.New(_get_enum("eSatellite"), name)
        return sat

    def get_object(self, path: str) -> Any:
        """
        通过路径检索子对象（如 ``"Satellite/Sat1"``）。

        Returns
        -------
        IAtkObject
        """
        return self._session.root.GetObjectFromPath(path)

    def get_satellites(self) -> list[Any]:
        """返回此场景中的所有卫星。"""
        children = self._scenario.GetChildren()
        return _collect_children_by_type(children, _get_enum("eSatellite"))

    # ------------------------------------------------------------------
    # 动画
    # ------------------------------------------------------------------

    def play(self) -> "ScenarioBuilder":
        """正向播放动画。"""
        self._scenario.GetRoot().GetAnimation().PlayForward()
        return self

    def reset(self) -> "ScenarioBuilder":
        """将动画重置到开始时间。"""
        self._scenario.GetRoot().GetAnimation().Reset()
        return self

    # ------------------------------------------------------------------
    # 字符串表示
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"<ScenarioBuilder name={self.name!r}>"


# ---------------------------------------------------------------------------
# 内部辅助方法
# ---------------------------------------------------------------------------

def _get_enum(name: str) -> Any:
    """从 ATK 模块解析传播器/对象枚举。"""
    from atk.component import session as _s
    return getattr(_s._ATK, name)


def _collect_children_by_type(collection: Any, etype: Any) -> list[Any]:
    """从 IAtkObjectCollection 中收集指定类型的所有子对象。"""
    results = []
    for i in range(collection.GetCount()):
        item = collection.Item(i)
        if item.GetClassType() == etype:
            results.append(item)
    return results
