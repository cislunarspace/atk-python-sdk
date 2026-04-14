"""
ATK Connect 模式 — 卫星构建器

提供流式 Python API，通过 Connect 命令创建和配置卫星。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from atk import exceptions as _ex
from atk import utils

if TYPE_CHECKING:
    from atk.connect.session import ATKConnection


# ---------------------------------------------------------------------------
# 传播器类型映射 — Connect 命令字符串 → ATK 传播器名称
# ---------------------------------------------------------------------------
_PROPAGATOR_CMD_MAP = {
    "PropagatorTwoBody":        "TwoBody",
    "PropagatorJ2Perturbation": "J2Perturbation",
    "PropagatorHPOP":          "HPOP",
    "PropagatorSGP4":          "SGP4",
    "PropagatorStkExternal":   "STKExternal",
    "PropagatorAstromaster":   "Astromaster",
    "PropagatorGreatArc":      "GreatArc",
    "PropagatorSimpleAscent":   "SimpleAscent",
    "PropagatorJ4Perturbation": "J4Perturbation",
    "PropagatorVinti":         "Vinti",
    "PropagatorBallistic":     "Ballistic",
}


class SatelliteBuilder:
    """
    Connect 模式下 ATK 卫星的流式构建器。

    通过 :meth:`ATKConnection.create_satellite() <atk.connect.session.ATKConnection.create_satellite>` 创建。

    示例::

        sat = atk.create_satellite('Sat1')
        sat.set_propagator('PropagatorAstromaster')
        sat.set_keplerian(sma=7100, ecc=0.001, inc=30, raan=0, argp=0, ta=0)
        sat.set_mass(500)
        sat.propagate(duration_days=1)
    """

    def __init__(
        self,
        conn: "ATKConnection",
        name: str,
        scenario_path: str = "*",
    ):
        self._conn = conn
        self._name = utils.validate_name(name)
        self._scenario_path = scenario_path
        # 此卫星的完整 ATK 路径
        self._path = f"{utils.resolve_path(scenario_path)}/Satellite/{self._name}"
        self._propagator: str | None = None

    # ------------------------------------------------------------------
    # 属性
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        return self._name

    @property
    def path(self) -> str:
        return self._path

    @property
    def propagator(self) -> str | None:
        return self._propagator

    # ------------------------------------------------------------------
    # 创建
    # ------------------------------------------------------------------

    def create(self) -> "SatelliteBuilder":
        """
        在 ATK 中创建卫星对象。

        使用 ATK 格式：``New / Satellite {name}``，obj='*'。
        """
        self._conn.send("New", "*", f" Satellite {self._name}")
        return self

    # ------------------------------------------------------------------
    # 传播器配置
    # ------------------------------------------------------------------

    def set_propagator(self, propagator: str) -> "SatelliteBuilder":
        """
        设置卫星的传播器类型。

        传播器在调用 :meth:`set_keplerian` 或 :meth:`set_cartesian` 时
        存储并应用，因为 ATK 使用 ``SetState`` 时嵌入传播器。

        Parameters
        ----------
        propagator : str
            传播器名称。有效名称：
            ``PropagatorTwoBody``、``PropagatorJ2Perturbation``、
            ``PropagatorHPOP``、``PropagatorSGP4``（通过 TLE）、
            ``PropagatorStkExternal``、``PropagatorAstromaster``、
            ``PropagatorGreatArc``、``PropagatorSimpleAscent``、
            ``PropagatorJ4Perturbation``、``PropagatorVinti``、
            ``PropagatorBallistic``。
        """
        if propagator not in _PROPAGATOR_CMD_MAP:
            raise _ex.ATKValueError(
                f"Unknown propagator {propagator!r}. "
                f"Valid names: {list(_PROPAGATOR_CMD_MAP)}"
            )
        self._propagator = _PROPAGATOR_CMD_MAP[propagator]
        return self

    # ------------------------------------------------------------------
    # 轨道状态 — 开普勒元素
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
        使用开普勒元素设置卫星的轨道状态。

        Parameters
        ----------
        sma : float
            半长轴（km）。正值为轨道，负值为双曲线。
        ecc : float
            离心率（0 ≤ ecc < 1 为椭圆）。
        inc : float
            轨道倾角（度）。
        raan : float
            升交点赤经（度）。
        argp : float
            近地点幅角（度）。
        ta : float
            真近点角（度）。
        epoch : str, optional
            ATK 格式的历元时间字符串（如 ``"1 Jan 2024 00:00:00.000"``）。

        Returns
        -------
        self
        """
        # ATK SetState Classical 传播器格式：
        # SetState */Satellite/{name} Classical {Propagator} "{start}" "{stop}"
        #   {Step} {CoordSys} "{epoch}" {SMA} {ECC} {INC} {RAAN} {ARGP} {TA}
        if epoch is None:
            epoch = "1 Jan 2024 00:00:00.000"
        prop = self._propagator or "TwoBody"
        stop = epoch  # 单点分析使用相同的历元作为开始和结束
        param = (
            f' Classical {prop} "{epoch}" "{stop}" '
            f'60 J2000 "{epoch}" {sma} {ecc} {inc} {raan} {argp} {ta}'
        )
        self._conn.send("SetState", self._path, param)
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
        使用笛卡尔坐标元素设置卫星的轨道状态。

        Parameters
        ----------
        x, y, z : float
            位置分量（km），在 J2000 坐标系中。
        vx, vy, vz : float
            速度分量（km/s），在 J2000 坐标系中。
        epoch : str, optional
            ATK 格式的历元时间字符串。

        Returns
        -------
        self
        """
        if epoch is None:
            epoch = "1 Jan 2024 00:00:00.000"
        prop = self._propagator or "TwoBody"
        stop = epoch
        param = (
            f' Cartesian {prop} "{epoch}" "{stop}" '
            f'60 J2000 "{epoch}" {x} {y} {z} {vx} {vy} {vz}'
        )
        self._conn.send("SetState", self._path, param)
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
        self._conn.send(
            "SetValue",
            self._path,
            f' "{self._path}/MassProperties.TotalMass" {total_mass}',
        )
        return self

    def set_stage_mass(
        self,
        dry_mass: float,
        wet_mass: float,
    ) -> "SatelliteBuilder":
        """
        设置卫星的干质量和湿质量（含推进剂），用于阶段建模。

        Returns
        -------
        self
        """
        self._conn.send(
            "SetValue",
            self._path,
            f' "{self._path}/MassProperties.DryMass" {dry_mass}',
        )
        self._conn.send(
            "SetValue",
            self._path,
            f' "{self._path}/MassProperties.WetMass" {wet_mass}',
        )
        return self

    # ------------------------------------------------------------------
    # 姿态
    # ------------------------------------------------------------------

    def set_attitude(
        self,
        attitude_type: str,
        q1: float = 0,
        q2: float = 0,
        q3: float = 0,
        q4: float = 1,
    ) -> "SatelliteBuilder":
        """
        设置卫星的姿态类型和可选四元数。

        Parameters
        ----------
        attitude_type : str
            ``"CBF"``、``"J2000"``、``"NV"``、``"TLE"`` 之一。
        q1-q4 : float
            四元数分量 (qx, qy, qz, qs)。默认为 (0,0,0,1) = 单位四元数。

        Returns
        -------
        self
        """
        valid_types = {"CBF", "J2000", "NV", "TLE"}
        if attitude_type not in valid_types:
            raise _ex.ATKValueError(
                f"Unknown attitude type {attitude_type!r}. Valid: {valid_types}"
            )
        self._conn.send("SetAttitude", self._path, f' "{attitude_type}" {q1} {q2} {q3} {q4}')
        return self

    # ------------------------------------------------------------------
    # 图形 / 可视化
    # ------------------------------------------------------------------

    def set_color(self, color_index: int) -> "SatelliteBuilder":
        """
        通过 ATK 颜色索引设置卫星的图形颜色。

        Parameters
        ----------
        color_index : int
            ATK 颜色表索引（0 = 默认，12 = 红色等）。

        Returns
        -------
        self
        """
        self._conn.send("Graphics", self._path, f" SetColor {color_index}")
        return self

    # ------------------------------------------------------------------
    # 运行 / 传播
    # ------------------------------------------------------------------

    def run_mcs(self) -> "SatelliteBuilder":
        """
        运行此卫星的任务控制序列 (MCS)。

        Returns
        -------
        self
        """
        self._conn.send("RunMCS", self._path, "")
        return self

    # ------------------------------------------------------------------
    # 字符串表示
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"<SatelliteBuilder name={self._name!r} path={self._path!r}>"
