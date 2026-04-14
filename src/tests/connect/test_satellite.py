"""
atk.connect.satellite 的单元测试 — SatelliteBuilder。
"""

import pytest
from unittest.mock import MagicMock


class MockATKConnection:
    """最小 ATKConnection 模拟。"""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str]] = []

    def send(self, command: str, obj_path: str = "*", param: str = "") -> MagicMock:
        self.calls.append((command, obj_path, param))
        result = MagicMock()
        result.m_vectData = "OK"
        return result


class TestSatelliteBuilder:
    """SatelliteBuilder 的测试。"""

    def test_create_satellite(self) -> None:
        from atk.connect.satellite import SatelliteBuilder

        conn = MockATKConnection()
        sat = SatelliteBuilder(conn, "Sat1")
        sat.create()

        # ATK 格式：obj='/', param=' Satellite {name}'
        # 合并后：'/ Satellite {name}'
        assert ("New", "/", " Satellite Sat1") in conn.calls

    def test_set_propagator(self) -> None:
        from atk.connect.satellite import SatelliteBuilder

        conn = MockATKConnection()
        sat = SatelliteBuilder(conn, "Sat1")
        sat.set_propagator("PropagatorAstromaster")

        # set_propagator() 现在仅存储传播器；不调用 send()
        assert len(conn.calls) == 0
        assert sat.propagator == "Astromaster"

    def test_invalid_propagator_raises(self) -> None:
        from atk.connect.satellite import SatelliteBuilder
        from atk import exceptions as atk_exc

        conn = MockATKConnection()
        sat = SatelliteBuilder(conn, "Sat1")

        with pytest.raises(atk_exc.ATKValueError, match="Unknown propagator"):
            sat.set_propagator("NotAPropagator")

    def test_set_keplerian(self) -> None:
        from atk.connect.satellite import SatelliteBuilder

        conn = MockATKConnection()
        sat = SatelliteBuilder(conn, "Sat1")
        sat.set_keplerian(sma=7100, ecc=0.001, inc=30, raan=0, argp=0, ta=180)

        # 使用 SetState Classical 格式
        setstate_calls = [c for c in conn.calls if c[0] == "SetState"]
        assert len(setstate_calls) == 1
        # 检查 Classical 格式包含 SMA
        assert " Classical " in setstate_calls[0][2]
        assert " 7100 " in setstate_calls[0][2] or " 7100" in setstate_calls[0][2]
        # SetState 后必须重置动画
        assert ("Animate", "*", " Reset") in conn.calls

    def test_set_state_tle(self) -> None:
        from atk.connect.satellite import SatelliteBuilder

        conn = MockATKConnection()
        sat = SatelliteBuilder(conn, "Sat1")
        line1 = "1 00005U 58002B   21084.26048267 -.00000099  00000-0 -13258-3 0  9992"
        line2 = "2 00005  34.2472  83.1377 1847466 176.0822 185.6710 10.84848342235752"
        sat.set_state_tle(line1, line2)

        setstate_calls = [c for c in conn.calls if c[0] == "SetState"]
        assert len(setstate_calls) == 1
        assert " TLE " in setstate_calls[0][2]
        assert line1 in setstate_calls[0][2]
        assert line2 in setstate_calls[0][2]
        # TLE SetState 后必须重置动画
        assert ("Animate", "*", " Reset") in conn.calls

    def test_set_mass(self) -> None:
        from atk.connect.satellite import SatelliteBuilder

        conn = MockATKConnection()
        sat = SatelliteBuilder(conn, "Sat1")
        sat.set_mass(total_mass=500.0)

        setvalue_calls = [c for c in conn.calls if c[0] == "SetValue"]
        assert any("TotalMass" in c[2] and "500" in c[2] for c in setvalue_calls)

    def test_run_mcs(self) -> None:
        from atk.connect.satellite import SatelliteBuilder

        conn = MockATKConnection()
        sat = SatelliteBuilder(conn, "Sat1")
        sat.run_mcs()

        assert ("RunMCS", "*/Satellite/Sat1", "") in conn.calls

    def test_invalid_attitude_raises(self) -> None:
        from atk.connect.satellite import SatelliteBuilder
        from atk import exceptions as atk_exc

        conn = MockATKConnection()
        sat = SatelliteBuilder(conn, "Sat1")

        with pytest.raises(atk_exc.ATKValueError, match="Unknown attitude type"):
            sat.set_attitude("NotAnAttitude")
