"""
ATK Component 模式 — 卫星构建器

用 Python 风格的流式 API 封装 ``ISatellite`` 和 ``IVADriverMCS``。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from atk import exceptions as _ex
from atk.component import session as _s

if TYPE_CHECKING:
    from atk.component.scenario import ScenarioBuilder


# 传播器字符串名称 → SWIG 枚举
_PROPAGATOR_MAP = {
    "PropagatorTwoBody":        "ePropagatorTwoBody",
    "PropagatorJ2Perturbation": "ePropagatorJ2Perturbation",
    "PropagatorHPOP":          "ePropagatorHPOP",
    "PropagatorSGP4":          "ePropagatorSGP4",
    "PropagatorStkExternal":   "ePropagatorStkExternal",
    "PropagatorAstromaster":   "ePropagatorAstromaster",
    "PropagatorGreatArc":      "ePropagatorGreatArc",
    "PropagatorSimpleAscent":   "ePropagatorSimpleAscent",
    "PropagatorJ4Perturbation": "ePropagatorJ4Perturbation",
    "PropagatorVinti":         "ePropagatorVinti",
    "PropagatorBallistic":     "ePropagatorBallistic",
}


class SatelliteBuilder:
    """
    ATK Component 模式下 ``ISatellite`` 的 Python 风格封装。

    通过 :meth:`ScenarioBuilder.create_satellite() <atk.component.scenario.ScenarioBuilder.create_satellite>` 创建。

    示例::

        sat = scenario.create_satellite('Sat1')
        sat.set_propagator_type('PropagatorAstromaster')
        sat.set_keplerian(sma=7100, ecc=0.001, inc=30, raan=0, argp=0, ta=0)
        mcs = sat.get_mcs_driver()
        ...
    """

    def __init__(self, sat: Any):
        self._sat = sat
        self._driver: Any | None = None

    # ------------------------------------------------------------------
    # 属性
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        return self._sat.GetInstanceName()

    @property
    def path(self) -> str:
        return self._sat.GetPath()

    @property
    def satellite(self) -> Any:
        """返回原始 ``ISatellite`` SWIG 对象。"""
        return self._sat

    # ------------------------------------------------------------------
    # 传播器配置
    # ------------------------------------------------------------------

    def set_propagator_type(self, propagator: str | Any) -> "SatelliteBuilder":
        """
        设置传播器类型。

        Parameters
        ----------
        propagator : str
            传播器名称（如 ``"PropagatorAstromaster"``）。
            或原始 SWIG 枚举值。
        """
        if isinstance(propagator, str):
            enum_name = _PROPAGATOR_MAP.get(propagator)
            if enum_name is None:
                raise _ex.ATKValueError(
                    f"Unknown propagator {propagator!r}. "
                    f"Valid names: {list(_PROPAGATOR_MAP)}"
                )
            enum = getattr(_s._ATK, enum_name)
        else:
            enum = propagator

        self._sat.SetPropagatorType(enum)
        self._driver = None  # 重置驱动器缓存
        return self

    def get_mcs_driver(self) -> Any:
        """
        获取此卫星的 MCS（任务控制序列）驱动器。

        Returns
        -------
        IVADriverMCS
        """
        if self._driver is None:
            self._driver = self._sat.GetPropagator()
        return self._driver

    # ------------------------------------------------------------------
    # 轨道状态
    # ------------------------------------------------------------------

    def set_keplerian(
        self,
        sma: float,
        ecc: float,
        inc: float,
        raan: float,
        argp: float,
        ta: float,
        epoch: str | None = None,
    ) -> "SatelliteBuilder":
        """
        通过 MCS 驱动器使用开普勒元素设置轨道状态。

        注意：此方法访问 MCS InitialState 段的属性。
        卫星必须先设置传播器。

        Parameters
        ----------
        sma : float
            半长轴（km）。
        ecc : float
            离心率。
        inc : float
            轨道倾角（度）。
        raan : float
            升交点赤经（度）。
        argp : float
            近地点幅角（度）。
        ta : float
            真近点角（度）。
        epoch : str, optional
            历元时间字符串。

        Returns
        -------
        self
        """
        driver = self.get_mcs_driver()
        seq = driver.GetMainSequence()
        seg_count = seq.GetCount()
        if seg_count == 0:
            raise _ex.ATKSatelliteError(
                "MCS has no segments. "
                "Use McsBuilder to build the segment sequence before setting state."
            )

        # 遍历段树以查找 InitialState 段
        # 第一个段通常是 InitialState 段
        seg = _find_initial_state_segment(seq)
        if seg is None:
            raise _ex.ATKSatelliteError("Could not find InitialState segment in MCS.")

        props = seg.GetProperties()
        if props is None:
            raise _ex.ATKSatelliteError("InitialState segment has no properties.")

        _set_segment_property(props, "sma", sma)
        _set_segment_property(props, "ecc", ecc)
        _set_segment_property(props, "inc", inc)
        _set_segment_property(props, "raan", raan)
        _set_segment_property(props, "argp", argp)
        _set_segment_property(props, "ta", ta)
        if epoch:
            _set_segment_property(props, "epoch", epoch)

        return self

    def set_cartesian(
        self,
        x: float,
        y: float,
        z: float,
        vx: float,
        vy: float,
        vz: float,
        epoch: str | None = None,
    ) -> "SatelliteBuilder":
        """
        使用笛卡尔坐标元素设置轨道状态。

        Returns
        -------
        self
        """
        # 类似 set_keplerian，但设置 CartesianX/Y/Z/VX/VY/VZ
        driver = self.get_mcs_driver()
        seq = driver.GetMainSequence()
        seg = _find_initial_state_segment(seq)
        if seg is None:
            raise _ex.ATKSatelliteError("Could not find InitialState segment in MCS.")
        props = seg.GetProperties()
        _set_segment_property(props, "CartesianX", x)
        _set_segment_property(props, "CartesianY", y)
        _set_segment_property(props, "CartesianZ", z)
        _set_segment_property(props, "CartesianVX", vx)
        _set_segment_property(props, "CartesianVY", vy)
        _set_segment_property(props, "CartesianVZ", vz)
        if epoch:
            _set_segment_property(props, "Epoch", epoch)
        return self

    # ------------------------------------------------------------------
    # 质量属性
    # ------------------------------------------------------------------

    def set_mass(self, total_mass: float) -> "SatelliteBuilder":
        """
        设置卫星的总质量（kg）。

        Returns
        -------
        self
        """
        mp = self._sat.GetMassProperties()
        mp.SetTotalMass(total_mass)
        return self

    def set_stage_mass(
        self,
        dry_mass: float,
        wet_mass: float,
    ) -> "SatelliteBuilder":
        """
        设置干质量和湿质量，用于阶段建模。

        Returns
        -------
        self
        """
        mp = self._sat.GetMassProperties()
        mp.SetDryMass(dry_mass)
        mp.SetPropellantMass(wet_mass - dry_mass)
        return self

    # ------------------------------------------------------------------
    # 姿态
    # ------------------------------------------------------------------

    def set_attitude_type(self, attitude_type: str | Any) -> "SatelliteBuilder":
        """
        设置卫星的姿态类型。

        Parameters
        ----------
        attitude_type : str
            姿态类型名称（如 ``"CBF"``、``"J2000"``）。
            或原始 SWIG 枚举值。
        """
        if isinstance(attitude_type, str):
            enum_name = f"eAttitude{attitude_type.capitalize()}"
            enum = getattr(_s._ATK, enum_name, None)
            if enum is None:
                raise _ex.ATKValueError(f"Unknown attitude type: {attitude_type!r}")
        else:
            enum = attitude_type

        self._sat.SetAttitudeType(enum)
        return self

    # ------------------------------------------------------------------
    # 图形
    # ------------------------------------------------------------------

    def set_color(self, color_index: int) -> "SatelliteBuilder":
        """
        通过 ATK 颜色索引设置卫星的图形颜色。

        Returns
        -------
        self
        """
        gfx = self._sat.GetGraphics()
        gfx.SetColor(color_index)
        return self

    # ------------------------------------------------------------------
    # 字符串表示
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"<SatelliteBuilder name={self.name!r}>"


# ---------------------------------------------------------------------------
# 内部辅助方法
# ---------------------------------------------------------------------------

def _find_initial_state_segment(seq: Any) -> Any | None:
    """
    遍历 MCS 段集合以查找 InitialState 段。

    返回找到的段或 None。
    """
    for i in range(seq.GetCount()):
        seg = seq.Item(i)
        seg_type = seg.GetType() if hasattr(seg, "GetType") else ""
        # 类型通常是字符串或枚举 — 检查是否包含 "InitialState"
        type_str = str(seg_type)
        if "InitialState" in type_str or "Initial" in type_str:
            return seg
    return None


def _set_segment_property(props: Any, name: str, value: float | str) -> None:
    """
    在 MCS 段属性对象上设置命名属性。

    使用 ATK Component API 中观察到的 SetValue / SetProperty 模式。
    """
    if hasattr(props, "SetValue"):
        props.SetValue(name, value)
    elif hasattr(props, f"Set{name}"):
        getattr(props, f"Set{name}")(value)
    else:
        # 最后手段 — 尝试 SetXxx 模式
        setter = getattr(props, f"Set{name}", None)
        if setter:
            setter(value)
        else:
            raise _ex.ATKMCSError(
                f"Segment properties object has no setter for {name!r}. "
                f"Available: {[a for a in dir(props) if a.startswith('Set')]}"
            )
