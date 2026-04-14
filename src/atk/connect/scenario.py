"""
ATK Connect 模式 — 场景构建器

提供流式 Python API，通过 Connect 命令创建和配置 ATK 场景。
"""

from __future__ import annotations

from typing import Any

from atk import exceptions as _ex
from atk import utils

from atk.connect.satellite import SatelliteBuilder
from atk.connect.session import ATKConnection


class ScenarioBuilder:
    """
    Connect 模式下 ATK 场景的流式构建器。

    通过 :meth:`ATKConnection.create_scenario() <atk.connect.session.ATKConnection.create_scenario>`
    创建，或直接调用 ``ScenarioBuilder(atk_conn, "ScenarioName")``。

    示例::

        scenario = atk.create_scenario('MyMission')
        scenario.set_analysis_period('1 Jan 2024 00:00:00', '7 Jan 2024 00:00:00')
        scenario.set_analysis_mode('Keplerian')
        scenario.save()
    """

    def __init__(self, conn: "ATKConnection", name: str):
        self._conn = conn
        self._name = utils.validate_name(name)
        # ATK Connect 中场景的路径
        self._path = f"*/Scenario/{self._name}"

    # ------------------------------------------------------------------
    # 属性
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        return self._name

    @property
    def path(self) -> str:
        return self._path

    # ------------------------------------------------------------------
    # 场景生命周期
    # ------------------------------------------------------------------

    def create(self) -> "ScenarioBuilder":
        """
        在 ATK 中设置（或创建）场景。

        ATK 启动时总会有一个默认场景已加载。
        ``New / Scenario {name}`` 会创建一个新场景，但如果已有场景
        加载则会失败。此方法优雅地处理此情况：如果场景已存在
        （New 返回 NACK），我们直接使用它 — ``set_analysis_period()``
        等操作无论哪个场景处于活动状态都能正常工作。

        Returns
        -------
        self
        """
        # ATK New 命令格式：obj='/', param=' Scenario {name}'
        # 合并后：'/ Scenario {name}'
        # 如果场景已加载，NACK 是预期行为 — 无需处理。
        try:
            self._conn.send("New", "/", f" Scenario {self._name}")
        except _ex.ATKCommandError:
            # 场景已存在；直接使用
            pass
        return self

    def save(self, path: str | None = None) -> "ScenarioBuilder":
        """
        将场景保存到文件。

        Parameters
        ----------
        path : str, optional
            保存路径。如果为 None，使用场景当前路径。

        Returns
        -------
        self
        """
        if path:
            self._conn.send("Save", self._path, f' "{path}"')
        else:
            self._conn.send("Save", self._path, "")
        return self

    def load(self, path: str) -> "ScenarioBuilder":
        """
        从 XML 文件加载场景。

        Parameters
        ----------
        path : str
            场景 XML 文件路径。

        Returns
        -------
        self
        """
        self._conn.send("Load", "*", f' "{path}"')
        return self

    def unload(self) -> "ScenarioBuilder":
        """从 ATK 内存中卸载场景。"""
        self._conn.send("Unload", self._path, "")
        return self

    # ------------------------------------------------------------------
    # 时间配置
    # ------------------------------------------------------------------

    def set_analysis_period(
        self,
        start: str,
        stop: str,
    ) -> "ScenarioBuilder":
        """
        设置场景的分析时间段。

        Parameters
        ----------
        start : str
            ATK 格式的开始时间（如 ``"5 Nov 2022 00:00:00.000"``）。
        stop : str
            ATK 格式的结束时间。

        Returns
        -------
        self
        """
        # 规范化路径：使用 '*' 表示全局（无特定场景）
        self._conn.send(
            "SetAnalysisTimePeriod",
            "*",
            f' "{start}" "{stop}"',
        )
        return self

    def set_analysis_mode(
        self,
        mode: str = "Keplerian",
    ) -> "ScenarioBuilder":
        """
        设置场景的分析模式。

        Parameters
        ----------
        mode : str
            ``"Keplerian"``、``"Spice"``、``"Fixed"`` 之一。

        Returns
        -------
        self
        """
        valid = {"Keplerian", "Spice", "Fixed"}
        if mode not in valid:
            raise _ex.ATKValueError(f"Invalid analysis mode {mode!r}. Must be one of {valid}.")
        self._conn.send("SetAnalysisMode", self._path, f' "{mode}"')
        return self

    # ------------------------------------------------------------------
    # 动画控制
    # ------------------------------------------------------------------

    def animate(self, forward: bool = True) -> "ScenarioBuilder":
        """
        启动场景动画。

        Parameters
        ----------
        forward : bool
            True 为正向播放（默认），False 为反向播放。

        Returns
        -------
        self
        """
        direction = "Forward" if forward else "Reverse"
        self._conn.send("Animate", self._path, f' "{direction}"')
        return self

    def stop_animation(self) -> "ScenarioBuilder":
        """停止场景动画。"""
        self._conn.send("Animate", self._path, ' "Stop"')
        return self

    # ------------------------------------------------------------------
    # 2D/3D 窗口
    # ------------------------------------------------------------------

    def open_2d_window(self, name: str = "2D") -> "ScenarioBuilder":
        """为此场景打开 2D 图形窗口。"""
        self._conn.send("Window2D", self._path, f' "{name}"')
        return self

    def open_3d_window(self, name: str = "3D") -> "ScenarioBuilder":
        """为此场景打开 3D 图形窗口。"""
        self._conn.send("Window3D", self._path, f' "{name}"')
        return self

    # ------------------------------------------------------------------
    # 报告快捷方式
    # ------------------------------------------------------------------

    def quick_report(
        self,
        obj_path: str,
        style: str,
        time_period: str | None = None,
    ) -> Any:
        """
        为对象生成快速报告。

        Parameters
        ----------
        obj_path : str
            场景内的对象路径。
        style : str
            报告样式名称。
        time_period : str, optional
            时间段字符串（如 ``"*"`` 表示全部时间）。

        Returns
        -------
        CMDRESULT
            原始 ATK 报告结果。参见 :mod:`atk.connect.reports` 获取
            更高级的封装。
        """
        if time_period:
            return self._conn.send(
                "QuickReport_" + style.replace(" ", ""),
                obj_path,
                f' {time_period}',
            )
        return self._conn.send(
            "QuickReport_" + style.replace(" ", ""),
            obj_path,
            "",
        )

    # ------------------------------------------------------------------
    # 字符串表示
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"<ScenarioBuilder name={self._name!r} path={self._path!r}>"


# ---------------------------------------------------------------------------
# ATKConnection 扩展 — 添加构建器工厂
# ---------------------------------------------------------------------------

def _scenario_builder_factory(conn: "ATKConnection", name: str) -> ScenarioBuilder:
    """创建并注册场景的 ScenarioBuilder。"""
    builder = ScenarioBuilder(conn, name)
    builder.create()
    return builder


def _satellite_builder_factory(conn: "ATKConnection", name: str, **kwargs) -> "SatelliteBuilder":
    """创建并注册卫星的 SatelliteBuilder。"""
    builder = SatelliteBuilder(conn, name, **kwargs)
    builder.create()
    return builder


# 猴子补丁 ATKConnection 以添加构建器方法（导入后应用）
def _patch_connection():
    from atk.connect import session as _s

    def create_scenario(self, name: str) -> ScenarioBuilder:
        """创建新场景并返回 ScenarioBuilder。"""
        return _scenario_builder_factory(self, name)

    def create_satellite(self, name: str, **kwargs) -> "SatelliteBuilder":
        """创建新卫星并返回 SatelliteBuilder。"""
        return _satellite_builder_factory(self, name, **kwargs)

    _s.ATKConnection.create_scenario = create_scenario
    _s.ATKConnection.create_satellite = create_satellite


_patch_connection()
del _patch_connection
