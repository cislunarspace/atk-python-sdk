"""
ATK Connect 模式 — 地面站和传感器构建器

提供流式 Python API，通过 Connect 命令创建和配置地面站（Facility）及其传感器（Sensor）。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from atk import exceptions as _ex
from atk import utils

if TYPE_CHECKING:
    from atk.connect.session import ATKConnection


class FacilityBuilder:
    """
    Connect 模式下 ATK 地面站（Facility）的流式构建器。

    通过 :meth:`ATKConnection.create_facility() <atk.connect.session.ATKConnection.create_facility>`
    创建。

    示例::

        facility = atk.create_facility('Beijing', lat=39.9, lon=116.4, height=50)
        facility.set_position(39.9, 116.4, 50)
        sensor = facility.create_sensor('Sensor1', el_start=5, el_end=85,
                                        az_start=0, az_end=360, max_range=2000)
    """

    def __init__(
        self,
        conn: "ATKConnection",
        name: str,
        lat: float = 0.0,
        lon: float = 0.0,
        height: float = 0.0,
    ):
        self._conn = conn
        self._name = utils.validate_name(name)
        self._path = f"*/Facility/{self._name}"
        self._lat = lat
        self._lon = lon
        self._height = height

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
    # 创建
    # ------------------------------------------------------------------

    def create(self) -> "FacilityBuilder":
        """
        在 ATK 中创建地面站对象。

        使用 ATK 格式：``New / Facility {name}``。
        """
        self._conn.send("New", "/", f" Facility {self._name}")
        return self

    # ------------------------------------------------------------------
    # 位置
    # ------------------------------------------------------------------

    def set_position(
        self,
        lat: float,
        lon: float,
        height: float = 0.0,
    ) -> "FacilityBuilder":
        """
        设置地面站的大地坐标（Geodetic）。

        Parameters
        ----------
        lat : float
            纬度（度，-90 ~ +90）。
        lon : float
            经度（度，-180 ~ +180）。
        height : float
            椭球高（米），默认 0.0。

        Returns
        -------
        self
        """
        if not (-90.0 <= lat <= 90.0):
            raise _ex.ATKValueError(
                f"Latitude must be between -90 and 90 degrees, got {lat}"
            )
        if not (-180.0 <= lon <= 180.0):
            raise _ex.ATKValueError(
                f"Longitude must be between -180 and 180 degrees, got {lon}"
            )
        self._lat = lat
        self._lon = lon
        self._height = height
        self._conn.send(
            "SetPosition",
            self._path,
            f" Geodetic {lat} {lon} {height}",
        )
        self._conn.send("Animate", "*", " Reset")
        return self

    # ------------------------------------------------------------------
    # 图形
    # ------------------------------------------------------------------

    def set_color(self, color_index: int) -> "FacilityBuilder":
        """
        通过 ATK 颜色索引设置地面站的图形颜色。

        Parameters
        ----------
        color_index : int
            ATK 颜色表索引。

        Returns
        -------
        self
        """
        self._conn.send("Graphics", self._path, f" SetColor {color_index}")
        return self

    # ------------------------------------------------------------------
    # 传感器
    # ------------------------------------------------------------------

    def create_sensor(
        self,
        name: str,
        el_start: float = 5.0,
        el_end: float = 85.0,
        az_start: float = 0.0,
        az_end: float = 360.0,
        max_range: float = 1000.0,
        pointing_euler: tuple[float, float, float] | None = None,
    ) -> "SensorBuilder":
        """
        在此地面站下创建并配置传感器。

        Parameters
        ----------
        name : str
            传感器名称。
        el_start, el_end : float
            俯仰角范围（度）。
        az_start, az_end : float
            方位角范围（度）。
        max_range : float
            最大作用距离（km）。
        pointing_euler : tuple, optional
            指向欧拉角 (a1, a2, a3)，默认 (180, 0, 0)。

        Returns
        -------
        SensorBuilder
        """
        builder = SensorBuilder(self._conn, name, self._name)
        builder.create()
        builder.define_conical(el_start, el_end, az_start, az_end)
        if pointing_euler is not None:
            builder.point_fixed_euler(123, *pointing_euler)
        else:
            builder.point_fixed_euler(123, 180, 0, 0)
        builder.set_range_constraint(max_range)
        return builder

    # ------------------------------------------------------------------
    # 字符串表示
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"<FacilityBuilder name={self._name!r} "
            f"lat={self._lat} lon={self._lon} height={self._height}>"
        )


class SensorBuilder:
    """
    Connect 模式下 ATK 传感器（Sensor）的流式构建器。

    通常通过 :meth:`FacilityBuilder.create_sensor()` 创建。
    """

    def __init__(
        self,
        conn: "ATKConnection",
        name: str,
        facility_name: str,
    ):
        self._conn = conn
        self._name = utils.validate_name(name)
        self._facility_name = facility_name
        self._path = f"*/Facility/{facility_name}/Sensor/{self._name}"

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
    # 创建
    # ------------------------------------------------------------------

    def create(self) -> "SensorBuilder":
        """
        在 ATK 中创建传感器对象。

        使用 ATK 格式：``New / */Facility/{parent}/Sensor {name}``。
        """
        self._conn.send(
            "New",
            "/",
            f" */Facility/{self._facility_name}/Sensor {self._name}",
        )
        return self

    # ------------------------------------------------------------------
    # 视场定义
    # ------------------------------------------------------------------

    def define_conical(
        self,
        el_start: float,
        el_end: float,
        az_start: float,
        az_end: float,
    ) -> "SensorBuilder":
        """
        定义复杂锥形视场。

        Parameters
        ----------
        el_start, el_end : float
            俯仰角范围（度）。
        az_start, az_end : float
            方位角范围（度）。

        Returns
        -------
        self
        """
        self._conn.send(
            "Define",
            self._path,
            f" Conical {el_start} {el_end} {az_start} {az_end}",
        )
        return self

    # ------------------------------------------------------------------
    # 指向
    # ------------------------------------------------------------------

    def point_fixed_euler(
        self,
        sequence: int,
        a1: float,
        a2: float,
        a3: float,
    ) -> "SensorBuilder":
        """
        设置固定指向（欧拉角方式）。

        Parameters
        ----------
        sequence : int
            欧拉角转序（如 123、321）。
        a1, a2, a3 : float
            欧拉角分量（度）。

        Returns
        -------
        self
        """
        self._conn.send(
            "Point",
            self._path,
            f" Fixed Euler {sequence} {a1} {a2} {a3}",
        )
        return self

    # ------------------------------------------------------------------
    # 约束
    # ------------------------------------------------------------------

    def set_range_constraint(self, max_range_km: float) -> "SensorBuilder":
        """
        设置最大作用距离约束。

        Parameters
        ----------
        max_range_km : float
            最大作用距离（km）。内部转换为米发送给 ATK。

        Returns
        -------
        self
        """
        max_range_m = max_range_km * 1000.0
        self._conn.send(
            "SetConstraint",
            self._path,
            f" Range Max {max_range_m}",
        )
        self._conn.send("Animate", "*", " Reset")
        return self

    # ------------------------------------------------------------------
    # 字符串表示
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"<SensorBuilder name={self._name!r} "
            f"facility={self._facility_name!r}>"
        )


# ---------------------------------------------------------------------------
# ATKConnection 扩展 — 添加 Facility 工厂
# ---------------------------------------------------------------------------

def _facility_builder_factory(
    conn: "ATKConnection",
    name: str,
    lat: float = 0.0,
    lon: float = 0.0,
    height: float = 0.0,
) -> FacilityBuilder:
    """创建并配置地面站的 FacilityBuilder。"""
    builder = FacilityBuilder(conn, name, lat, lon, height)
    builder.create()
    builder.set_position(lat, lon, height)
    return builder


def _patch_connection():
    from atk.connect import session as _s

    def create_facility(
        self,
        name: str,
        lat: float = 0.0,
        lon: float = 0.0,
        height: float = 0.0,
    ) -> FacilityBuilder:
        """创建地面站并返回 FacilityBuilder。"""
        return _facility_builder_factory(self, name, lat, lon, height)

    _s.ATKConnection.create_facility = create_facility


_patch_connection()
del _patch_connection
