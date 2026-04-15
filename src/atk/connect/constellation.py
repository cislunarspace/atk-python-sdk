"""
ATK Connect 模式 — 星座构建器与批量操作

提供 Walker 星座模式生成和多卫星分析的批量操作。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from atk import exceptions as _ex
from atk import utils
from atk.connect.satellite import _PROPAGATOR_CMD_MAP

if TYPE_CHECKING:
    from atk.connect.session import ATKConnection


class WalkerBuilder:
    """
    使用 Walker Delta 模式构建星座。

    参考文献：Walker, J.G. (1971) "Satellite constellations"。
    模式表示法：``T/P/F``，其中 T=卫星总数，P=轨道面数，F=相位因子。

    示例::

        walker = atk.constellation_builder('Starlink')
        walker.walker_delta(
            num_satellites=60,
            num_planes=6,
            inc=53.0,
            alt=550.0,
        )
        walker.set_propagator('PropagatorSGP4')
        walker.run_all()
    """

    def __init__(
        self,
        conn: "ATKConnection",
        constellation_name: str,
        scenario_path: str = "*",
    ):
        self._conn = conn
        self._name = utils.validate_name(constellation_name)
        self._scenario_path = utils.resolve_path(scenario_path)
        self._path_prefix = f"{self._scenario_path}/Constellation/{self._name}"

        self._num_satellites = 0
        self._num_planes = 0
        self._inc = 0.0
        self._alt = 0.0
        self._phase_ratio = 0.0
        self._propagator = "TwoBody"
        self._sma: float | None = None
        self._created = False

    # ------------------------------------------------------------------
    # Walker Delta 配置
    # ------------------------------------------------------------------

    def walker_delta(
        self,
        num_satellites: int,
        num_planes: int,
        inc: float,
        alt: float,
    ) -> "WalkerBuilder":
        """
        配置 Walker Delta 星座。

        Parameters
        ----------
        num_satellites : int
            卫星总数 (T)。
        num_planes : int
            轨道面数 (P)。必须能整除 T。
        inc : float
            轨道倾角（度）。
        alt : float
            轨道高度（km）。

        Returns
        -------
        self
        """
        if num_satellites <= 0 or num_planes <= 0:
            raise _ex.ATKValueError(
                f"num_satellites and num_planes must be positive, "
                f"got {num_satellites}, {num_planes}"
            )
        if num_satellites % num_planes != 0:
            raise _ex.ATKValueError(
                f"num_satellites ({num_satellites}) must be divisible "
                f"by num_planes ({num_planes})"
            )

        self._num_satellites = num_satellites
        self._num_planes = num_planes
        self._inc = inc
        self._alt = alt

        # 相位比 F = 每面卫星数 / (1 + 每面卫星数)
        sats_per_plane = num_satellites // num_planes
        self._phase_ratio = sats_per_plane / (num_planes * (sats_per_plane - 1) + 1)

        # 从高度近似计算 SMA（圆轨道，地球半径约 6371 km）
        self._sma = alt + 6371.0

        return self

    def set_propagator(self, propagator: str) -> "WalkerBuilder":
        """
        设置星座中所有卫星的传播器类型。

        Returns
        -------
        self
        """
        if propagator not in _PROPAGATOR_CMD_MAP:
            raise _ex.ATKValueError(
                f"Unknown propagator {propagator!r}. "
                f"Valid names: {list(_PROPAGATOR_CMD_MAP)}"
            )
        self._propagator = _PROPAGATOR_CMD_MAP[propagator]
        return self

    # ------------------------------------------------------------------
    # 构建
    # ------------------------------------------------------------------

    def build(self) -> "WalkerBuilder":
        """
        生成星座 — 创建星座容器和所有卫星对象及其轨道元素。

        Returns
        -------
        self
        """
        if self._created:
            return self

        # 创建星座容器：New / Constellation/{name}，obj='/'
        self._conn.send("New", "/", f" Constellation/{self._name}")
        self._created = True

        sats_per_plane = self._num_satellites // self._num_planes
        epoch = "1 Jan 2024 00:00:00.000"
        prop = self._propagator or "TwoBody"

        for sat_idx in range(self._num_satellites):
            plane_idx = sat_idx // sats_per_plane
            intra_plane_idx = sat_idx % sats_per_plane

            # RAAN 间距：360 / 轨道面数，每个面
            raan = (360.0 / self._num_planes) * plane_idx

            # 相位偏移：(360 / 卫星总数) * 相位比 * 面内索引
            # 应用于每个面的偏移
            phase_offset = (360.0 / self._num_satellites) * self._phase_ratio * plane_idx
            ta = (360.0 / sats_per_plane) * intra_plane_idx + phase_offset

            sat_name = f"{self._name}_P{plane_idx}_S{intra_plane_idx}"
            sat_path = f"*/Constellation/{self._name}/Satellite/{sat_name}"

            # 创建卫星：New / Satellite {name}，obj='/'（在星座根目录下创建）
            self._conn.send("New", "/", f" Satellite {sat_name}")

            # 通过 SetState Classical {prop} 设置开普勒元素
            stop = epoch
            param = (
                f' Classical {prop} "{epoch}" "{stop}" '
                f'60 J2000 "{epoch}" {self._sma} 0.0 {self._inc} {raan} 0.0 {ta}'
            )
            self._conn.send("SetState", sat_path, param)

        return self

    # ------------------------------------------------------------------
    # 批量 MCS 运行
    # ------------------------------------------------------------------

    def run_all(self) -> dict[str, bool]:
        """
        串行运行星座中所有卫星的 MCS。

        注意：ATK Connect 模式的 TCP 连接不支持并发访问，
        因此使用串行执行以确保线程安全。

        Returns
        -------
        dict[str, bool]
            卫星名称 → 成功 (True) 或失败 (False) 的映射。
        """
        if not self._created:
            raise _ex.ATKError(
                "Call build() before run_all()."
            )

        sats_per_plane = self._num_satellites // self._num_planes
        results: dict[str, bool] = {}

        for sat_idx in range(self._num_satellites):
            plane_idx = sat_idx // sats_per_plane
            intra_plane_idx = sat_idx % sats_per_plane
            sat_name = f"{self._name}_P{plane_idx}_S{intra_plane_idx}"
            sat_path = f"{self._path_prefix}/Satellite/{sat_name}"
            try:
                self._conn.send("RunMCS", sat_path, "")
                results[sat_name] = True
            except _ex.ATKError as exc:
                results[sat_name] = False
                import warnings
                warnings.warn(
                    f"MCS run failed for {sat_name}: {exc}",
                    RuntimeWarning,
                    stacklevel=2,
                )

        return results

    @property
    def satellite_count(self) -> int:
        return self._num_satellites

    def __repr__(self) -> str:
        return (
            f"<WalkerBuilder name={self._name!r} "
            f"sats={self._num_satellites} planes={self._num_planes} "
            f"inc={self._inc} alt={self._alt}>"
        )


# ---------------------------------------------------------------------------
# 将 constellation_builder() 添加到 ATKConnection
# ---------------------------------------------------------------------------

def _patch_connection():
    from atk.connect import session as _s

    def constellation_builder(self, name: str) -> WalkerBuilder:
        """创建 Walker 星座构建器。"""
        return WalkerBuilder(self, name)

    _s.ATKConnection.constellation_builder = constellation_builder


_patch_connection()
del _patch_connection
