"""
ATK Connect 模式 — 覆盖分析辅助工具

提供流式 API，用于创建覆盖定义、添加资产/地面站，
以及计算访问统计。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from atk import exceptions as _ex
from atk import utils

if TYPE_CHECKING:
    from atk.connect.session import ATKConnection


class CoverageBuilder:
    """
    ATK CoverageDefinition 对象的流式构建器。

    通过 ``atk.create_coverage('CoverageName')`` 创建。

    示例::

        cov = atk.create_coverage('GroundCoverage')
        cov.add_asset('*/Satellite/Sat1')
        cov.add_facility('*/Facility/Station1')
        cov.set_grid_resolution(lat_step=1.0, lon_step=1.0)
        stats = cov.compute_stats()
    """

    def __init__(self, conn: "ATKConnection", name: str):
        self._conn = conn
        self._name = utils.validate_name(name)
        self._path = f"*/CoverageDefinition/{self._name}"
        self._assets: list[str] = []
        self._facilities: list[str] = []

    @property
    def name(self) -> str:
        return self._name

    @property
    def path(self) -> str:
        return self._path

    def create(self) -> "CoverageBuilder":
        """在 ATK 中创建覆盖定义对象。"""
        self._conn.send("New", self._path, "")
        return self

    def add_asset(self, sat_path: str) -> "CoverageBuilder":
        """
        添加卫星作为覆盖资产。

        Parameters
        ----------
        sat_path : str
            卫星的 ATK 路径（如 ``"*/Satellite/Sat1"``）。

        Returns
        -------
        self
        """
        sat_path = utils.resolve_path(sat_path)
        self._assets.append(sat_path)
        # ATK format: Cov */CoverageDefinition/{name} Asset {sat_path} Assign
        self._conn.send("Cov", self._path, f" Asset {sat_path} Assign")
        return self

    def add_facility(self, facility_path: str) -> "CoverageBuilder":
        """
        添加地面站作为覆盖目标。

        Parameters
        ----------
        facility_path : str
            地面站的 ATK 路径（如 ``"*/Facility/Station1"``）。

        Returns
        -------
        self
        """
        facility_path = utils.resolve_path(facility_path)
        self._facilities.append(facility_path)
        # ATK format: Cov */CoverageDefinition/{name} Facility {facility_path} Assign
        self._conn.send("Cov", self._path, f" Facility {facility_path} Assign")
        return self

    def set_grid_resolution(
        self,
        lat_step: float = 1.0,
        lon_step: float = 1.0,
        grid_type: str = "LatLon",
    ) -> "CoverageBuilder":
        """
        设置覆盖网格分辨率。

        Parameters
        ----------
        lat_step : float
            纬度步长（度）。
        lon_step : float
            经度步长（度）。
        grid_type : str
            网格类型（如 ``"LatLon"``、``"Custom"``）。

        Returns
        -------
        self
        """
        self._conn.send(
            "Cov",
            self._path,
            f' Grid "{grid_type}" {lat_step} {lon_step}',
        )
        return self

    def set_fom(
        self,
        fom_name: str,
        asset_path: str | None = None,
    ) -> "CoverageBuilder":
        """
        将品质因数 (FOM) 附加到覆盖定义。

        Parameters
        ----------
        fom_name : str
            FOM 名称（如 ``"SimpleAER"``、``"Distance"``）。
        asset_path : str, optional
            FOM 的资产路径。

        Returns
        -------
        self
        """
        if asset_path:
            self._conn.send(
                "Cov",
                self._path,
                f' FOM "{fom_name}" "{utils.resolve_path(asset_path)}"',
            )
        else:
            self._conn.send("Cov", self._path, f' FOM "{fom_name}"')
        return self

    def compute_stats(
        self,
        time_period: str = "*",
    ) -> CoverageStats:
        """
        计算覆盖统计。

        Parameters
        ----------
        time_period : str
            时间段字符串（如 ``"*"`` 表示全部时间）。

        Returns
        -------
        CoverageStats
            包含访问次数、总访问时间等的对象。
        """
        raw = self._conn.send("Cov", self._path, f" Compute {time_period}")
        return CoverageStats(raw)

    def __repr__(self) -> str:
        return f"<CoverageBuilder name={self._name!r}>"


class CoverageStats:
    """
    解析后的覆盖计算结果。

    Attributes
    ----------
    raw : CMDRESULT
        原始 ATK 结果对象。
    access_count : int
        访问区间数量。
    total_access_time : float
        总访问时间（秒）。
    mean_access_duration : float
        每次访问区间的平均持续时间。
    """

    def __init__(self, raw):
        self.raw = raw
        self._data = utils.result_to_list(raw)
        self._parsed = self._parse()

    def _parse(self) -> dict:
        """将原始 CMDRESULT 数据解析为字典。"""
        data = self._data
        if not data:
            return {}
        # 优先尝试 key=value 格式
        result = {}
        positional = []
        for item in data:
            if "=" in item:
                key, val = item.split("=", 1)
                result[key.strip()] = val.strip()
            else:
                positional.append(item)
        # 如果既没有 key=value 也没有足够的 position 数据，抛出异常
        if not result and len(positional) < 3:
            raise _ex.ATKError(
                f"Unexpected CoverageStats format, expected 'key=value' pairs or "
                f"at least 3 positional values, got: {data}"
            )
        # 如果没有 key=value 对，尝试位置解析
        if not result and len(positional) >= 3:
            # [count, total_time, mean_dur, ...]
            try:
                int(positional[0])
                float(positional[1])
                float(positional[2])
            except (ValueError, TypeError):
                raise _ex.ATKError(
                    f"Unexpected CoverageStats format, expected 'key=value' pairs or "
                    f"at least 3 positional numeric values, got: {data}"
                )
            result["AccessCount"] = positional[0]
            result["TotalAccessTime"] = positional[1]
            result["MeanAccessDuration"] = positional[2] if len(positional) > 2 else "0"
        return result

    @property
    def access_count(self) -> int:
        try:
            return int(self._parsed.get("AccessCount", 0))
        except (ValueError, TypeError) as exc:
            raise _ex.ATKError(f"Failed to parse access_count: {exc}") from exc

    @property
    def total_access_time(self) -> float:
        try:
            return float(self._parsed.get("TotalAccessTime", 0.0))
        except (ValueError, TypeError) as exc:
            raise _ex.ATKError(f"Failed to parse total_access_time: {exc}") from exc

    @property
    def mean_access_duration(self) -> float:
        try:
            return float(self._parsed.get("MeanAccessDuration", 0.0))
        except (ValueError, TypeError) as exc:
            raise _ex.ATKError(f"Failed to parse mean_access_duration: {exc}") from exc

    def __repr__(self) -> str:
        return (
            f"<CoverageStats access_count={self.access_count} "
            f"total_time={self.total_access_time:.2f}s>"
        )


# ---------------------------------------------------------------------------
# 将 create_coverage() 添加到 ATKConnection
# ---------------------------------------------------------------------------

def _patch_connection():
    from atk.connect import session as _s

    def create_coverage(self, name: str) -> CoverageBuilder:
        """创建新的 CoverageDefinition 并返回 CoverageBuilder。"""
        builder = CoverageBuilder(self, name)
        builder.create()
        return builder

    _s.ATKConnection.create_coverage = create_coverage


_patch_connection()
del _patch_connection
