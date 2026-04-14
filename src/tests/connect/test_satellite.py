"""
Unit tests for atk.connect.satellite — SatelliteBuilder.
"""

import pytest
from unittest.mock import MagicMock


class MockATKConnection:
    """Minimal ATKConnection mock."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str]] = []

    def send(self, command: str, obj_path: str = "*", param: str = "") -> MagicMock:
        self.calls.append((command, obj_path, param))
        result = MagicMock()
        result.m_vectData = "OK"
        return result


class TestSatelliteBuilder:
    """Tests for SatelliteBuilder."""

    def test_create_satellite(self) -> None:
        from atk.connect.satellite import SatelliteBuilder

        conn = MockATKConnection()
        sat = SatelliteBuilder(conn, "Sat1")
        sat.create()

        # ATK format: obj='*', param=' Satellite {name}'
        assert ("New", "*", " Satellite Sat1") in conn.calls

    def test_set_propagator(self) -> None:
        from atk.connect.satellite import SatelliteBuilder

        conn = MockATKConnection()
        sat = SatelliteBuilder(conn, "Sat1")
        sat.set_propagator("PropagatorAstromaster")

        # set_propagator() now stores the propagator; no send() calls made
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

        # Uses SetState with Classical format
        setstate_calls = [c for c in conn.calls if c[0] == "SetState"]
        assert len(setstate_calls) == 1
        # Check Classical format includes SMA
        assert " Classical " in setstate_calls[0][2]
        assert " 7100 " in setstate_calls[0][2] or " 7100" in setstate_calls[0][2]

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
