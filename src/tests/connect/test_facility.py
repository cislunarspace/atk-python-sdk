"""
atk.connect.facility 的单元测试 — FacilityBuilder 和 SensorBuilder。
"""

import pytest
from unittest.mock import MagicMock

from tests.connect.conftest import MockATKConnection


class TestFacilityBuilder:
    """FacilityBuilder 的测试。"""

    def test_create_facility(self) -> None:
        from atk.connect.facility import FacilityBuilder

        conn = MockATKConnection()
        fac = FacilityBuilder(conn, "Beijing", lat=39.9, lon=116.4, height=50)
        fac.create()

        assert ("New", "/", " Facility Beijing") in conn.calls

    def test_set_position(self) -> None:
        from atk.connect.facility import FacilityBuilder

        conn = MockATKConnection()
        fac = FacilityBuilder(conn, "Beijing")
        fac.set_position(39.9, 116.4, 50)

        setpos_calls = [c for c in conn.calls if c[0] == "SetPosition"]
        assert len(setpos_calls) == 1
        assert " Geodetic 39.9 116.4 50" == setpos_calls[0][2]
        assert ("Animate", "*", " Reset") in conn.calls

    def test_set_position_rejects_invalid_lat(self):
        from atk.connect.facility import FacilityBuilder
        from atk import exceptions as atk_exc

        conn = MockATKConnection()
        fac = FacilityBuilder(conn, "Station1")

        with pytest.raises(atk_exc.ATKValueError, match="between -90 and 90"):
            fac.set_position(lat=95.0, lon=0.0, height=0.0)

    def test_set_position_rejects_invalid_lon(self):
        from atk.connect.facility import FacilityBuilder
        from atk import exceptions as atk_exc

        conn = MockATKConnection()
        fac = FacilityBuilder(conn, "Station1")

        with pytest.raises(atk_exc.ATKValueError, match="between -180 and 180"):
            fac.set_position(lat=0.0, lon=200.0, height=0.0)

    def test_set_color(self) -> None:
        from atk.connect.facility import FacilityBuilder

        conn = MockATKConnection()
        fac = FacilityBuilder(conn, "Beijing")
        fac.set_color(5)

        assert ("Graphics", "*/Facility/Beijing", " SetColor 5") in conn.calls

    def test_create_sensor(self) -> None:
        from atk.connect.facility import FacilityBuilder

        conn = MockATKConnection()
        fac = FacilityBuilder(conn, "Beijing")
        sensor = fac.create_sensor(
            "Sensor1",
            el_start=5,
            el_end=85,
            az_start=0,
            az_end=360,
            max_range=2000,
        )

        # 检查传感器创建命令
        new_calls = [c for c in conn.calls if c[0] == "New"]
        assert any("Sensor Sensor1" in c[2] for c in new_calls)

        # 检查 Define Conical 命令
        define_calls = [c for c in conn.calls if c[0] == "Define"]
        assert len(define_calls) == 1
        assert " Conical 5 85 0 360" == define_calls[0][2]

        # 检查 Point Fixed Euler 命令
        point_calls = [c for c in conn.calls if c[0] == "Point"]
        assert len(point_calls) == 1
        assert " Fixed Euler 123 180 0 0" == point_calls[0][2]

        # 检查 SetConstraint Range Max（km → m）
        constraint_calls = [c for c in conn.calls if c[0] == "SetConstraint"]
        assert len(constraint_calls) == 1
        assert " Range Max 2000000.0" == constraint_calls[0][2]

        # 检查传感器路径
        assert sensor.path == "*/Facility/Beijing/Sensor/Sensor1"


class TestSensorBuilder:
    """SensorBuilder 的测试。"""

    def test_create_sensor(self) -> None:
        from atk.connect.facility import SensorBuilder

        conn = MockATKConnection()
        sensor = SensorBuilder(conn, "S1", "Station1")
        sensor.create()

        assert ("New", "/", " */Facility/Station1/Sensor S1") in conn.calls

    def test_define_conical(self) -> None:
        from atk.connect.facility import SensorBuilder

        conn = MockATKConnection()
        sensor = SensorBuilder(conn, "S1", "Station1")
        sensor.define_conical(5, 85, 0, 360)

        define_calls = [c for c in conn.calls if c[0] == "Define"]
        assert len(define_calls) == 1
        assert " Conical 5 85 0 360" == define_calls[0][2]

    def test_point_fixed_euler(self) -> None:
        from atk.connect.facility import SensorBuilder

        conn = MockATKConnection()
        sensor = SensorBuilder(conn, "S1", "Station1")
        sensor.point_fixed_euler(321, 10, 20, 30)

        point_calls = [c for c in conn.calls if c[0] == "Point"]
        assert len(point_calls) == 1
        assert " Fixed Euler 321 10 20 30" == point_calls[0][2]

    def test_set_range_constraint(self) -> None:
        from atk.connect.facility import SensorBuilder

        conn = MockATKConnection()
        sensor = SensorBuilder(conn, "S1", "Station1")
        sensor.set_range_constraint(500)

        constraint_calls = [c for c in conn.calls if c[0] == "SetConstraint"]
        assert len(constraint_calls) == 1
        assert " Range Max 500000.0" == constraint_calls[0][2]
        assert ("Animate", "*", " Reset") in conn.calls
