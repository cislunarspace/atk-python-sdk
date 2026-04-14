"""
ATK Component 模式 — MCS（任务控制序列）构建器

提供流式 API，通过 SWIG 封装的 IVADriverMCS / IVAMCSSegmentCollection
构建 Astrogator MCS 段序列。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from atk import exceptions as _ex
if TYPE_CHECKING:
    from atk.component.satellite import SatelliteBuilder


class McsBuilder:
    """
    Component 模式下 Astrogator MCS 段的流式构建器。

    通过 :meth:`SatelliteBuilder.get_mcs_driver()
    <atk.component.satellite.SatelliteBuilder.get_mcs_driver>` 获取驱动器，
    然后调用 :meth:`driver.main_sequence()
    <IVADriverMCS.main_sequence>` 获取构建器，或直接实例化此类::

        sat = scenario.create_satellite('Sat1')
        sat.set_propagator_type('PropagatorAstromaster')
        mcs = McsBuilder(sat)
        mcs.initial_state_keplerian(sma=6678, ecc=0, inc=28.5, ...)
        mcs.propagate_until('10 Jan 2024 12:00:00')
        mcs.run()

    Attributes
    ----------
    driver : IVADriverMCS
        从卫星获取的 MCS 驱动器。
    """

    def __init__(self, sat_or_driver: Any):
        """
        Parameters
        ----------
        sat_or_driver : ISatellite 或 IVADriverMCS
            卫星或已获取的传播器驱动器。
        """
        # 接受 ISatellite 或 IVADriverMCS
        self._driver: Any = None
        self._seq: Any = None
        self._seg_count = 0

        if hasattr(sat_or_driver, "GetPropagator"):
            # 是 ISatellite
            self._driver = sat_or_driver.GetPropagator()
        elif hasattr(sat_or_driver, "GetMainSequence"):
            # 已经是 IVADriverMCS
            self._driver = sat_or_driver
        else:
            raise _ex.ATKMCSError(
                f"Expected ISatellite or IVADriverMCS, got {type(sat_or_driver).__name__}"
            )

        self._seq = self._driver.GetMainSequence()
        self._seg_count = self._seq.GetCount() if self._seq else 0

    # ------------------------------------------------------------------
    # 属性
    # ------------------------------------------------------------------

    @property
    def driver(self) -> Any:
        return self._driver

    @property
    def segment_count(self) -> int:
        """当前序列中的段数量。"""
        return self._seg_count

    # ------------------------------------------------------------------
    # 段构建器
    # ------------------------------------------------------------------

    def initial_state_keplerian(
        self,
        sma: float,
        ecc: float,
        inc: float,
        raan: float,
        argp: float,
        ta: float,
        epoch: str | None = None,
    ) -> "McsBuilder":
        """
        添加一个带开普勒元素的 InitialState 段。

        Returns
        -------
        self
        """
        seg = self._append_segment("Initial_State")
        props = seg.GetProperties()
        _set_prop(props, "sma", sma)
        _set_prop(props, "ecc", ecc)
        _set_prop(props, "inc", inc)
        _set_prop(props, "raan", raan)
        _set_prop(props, "argp", argp)
        _set_prop(props, "ta", ta)
        if epoch:
            _set_prop(props, "epoch", epoch)
        return self

    def initial_state_cartesian(
        self,
        x: float, y: float, z: float,
        vx: float, vy: float, vz: float,
        epoch: str | None = None,
    ) -> "McsBuilder":
        """
        添加一个带笛卡尔坐标元素的 InitialState 段。

        Returns
        -------
        self
        """
        seg = self._append_segment("Initial_State")
        props = seg.GetProperties()
        _set_prop(props, "CartesianX", x)
        _set_prop(props, "CartesianY", y)
        _set_prop(props, "CartesianZ", z)
        _set_prop(props, "CartesianVX", vx)
        _set_prop(props, "CartesianVY", vy)
        _set_prop(props, "CartesianVZ", vz)
        if epoch:
            _set_prop(props, "Epoch", epoch)
        return self

    def propagate_until(
        self,
        stop_time: str,
        time_step: float = 60.0,
    ) -> "McsBuilder":
        """
        添加一个 Propagate 段。

        Parameters
        ----------
        stop_time : str
            ATK 格式的停止时间。
        time_step : float
            传播时间步长（秒）。

        Returns
        -------
        self
        """
        seg = self._append_segment("Propagate")
        props = seg.GetProperties()
        _set_prop(props, "StopTime", stop_time)
        _set_prop(props, "TimeStep", time_step)
        return self

    def propagate_duration(
        self,
        duration_seconds: float,
        time_step: float = 60.0,
    ) -> "McsBuilder":
        """
        添加一个指定持续时间的 Propagate 段。

        Returns
        -------
        self
        """
        seg = self._append_segment("Propagate")
        props = seg.GetProperties()
        _set_prop(props, "Duration", duration_seconds)
        _set_prop(props, "TimeStep", time_step)
        return self

    def impulsive_burn(
        self,
        dv: tuple[float, float, float] | list[float],
        direction: str = "CartesianX",
    ) -> "McsBuilder":
        """
        添加一个 ImpulsiveBurn 段。

        Parameters
        ----------
        dv : tuple/list，包含 3 个浮点数
            Delta-V 分量。
        direction : str
            点火方向。默认 ``"CartesianX"``。

        Returns
        -------
        self
        """
        if len(dv) != 3:
            raise _ex.ATKValueError(f"dv must have 3 components, got {len(dv)}")
        seg = self._append_segment("ImpulsiveBurn")
        props = seg.GetProperties()
        _set_prop(props, "dvX", dv[0])
        _set_prop(props, "dvY", dv[1])
        _set_prop(props, "dvZ", dv[2])
        _set_prop(props, "Direction", direction)
        return self

    def target_sequence(
        self,
        endpoint_path: str,
        tolerance: float = 1e-6,
    ) -> "McsBuilder":
        """
        添加一个 TargetSequence 段。

        Returns
        -------
        self
        """
        seg = self._append_segment("TargetSequence")
        props = seg.GetProperties()
        _set_prop(props, "Endpoint", endpoint_path)
        _set_prop(props, "Tolerance", tolerance)
        return self

    # ------------------------------------------------------------------
    # 运行 / 应用
    # ------------------------------------------------------------------

    def run(self) -> "McsBuilder":
        """运行 MCS。"""
        self._driver.RunMCS()
        return self

    def apply_changes(self) -> "McsBuilder":
        """应用所有待处理的配置变更。"""
        self._driver.ApplyAllProfileChanges()
        return self

    def reset_profiles(self) -> "McsBuilder":
        """将所有配置重置为初始状态。"""
        self._driver.ResetAllProfiles()
        return self

    # ------------------------------------------------------------------
    # 内部辅助方法
    # ------------------------------------------------------------------

    def _append_segment(self, seg_type: str) -> Any:
        """
        向主序列追加指定类型的新段。

        返回新创建的段对象。
        """
        # IVAMCSSegmentCollection.AppendSegment(type_name)
        seg = self._seq.AppendSegment(seg_type)
        self._seg_count += 1
        return seg

    def __repr__(self) -> str:
        return f"<McsBuilder segments={self._seg_count}>"


# ---------------------------------------------------------------------------
# 内部属性设置辅助函数
# ---------------------------------------------------------------------------

def _set_prop(props: Any, name: str, value: float | str) -> None:
    """
    在 MCS 段属性对象上设置属性。

    优先尝试 SetValue，然后尝试 SetXxx(name) 设置模式。
    """
    if hasattr(props, "SetValue"):
        props.SetValue(name, value)
    else:
        # 尝试 SetXxx 模式
        setter = getattr(type(props), f"Set{name}", None)
        if setter:
            setter(props, value)
        else:
            raise _ex.ATKMCSError(
                f"Cannot set property {name!r} on segment properties. "
                f"Available methods: {[m for m in dir(props) if m.startswith('Set')]}"
            )
