"""
Unit tests for atk.connect.scenario — ScenarioBuilder.
"""

import pytest
from unittest.mock import MagicMock, patch


class MockATKConnection:
    """Minimal ATKConnection mock for ScenarioBuilder tests."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str]] = []
        self._connected = True

    def send(self, command: str, obj_path: str = "*", param: str = "") -> MagicMock:
        self.calls.append((command, obj_path, param))
        result = MagicMock()
        result.m_vectData = "OK"
        return result

    @property
    def is_connected(self) -> bool:
        return self._connected


class TestScenarioBuilder:
    """Tests for ScenarioBuilder."""

    def test_create_scenario(self) -> None:
        from atk.connect.scenario import ScenarioBuilder

        conn = MockATKConnection()
        builder = ScenarioBuilder(conn, "MyScenario")
        builder.create()

        # ATK format: obj='*', param=' Scenario {name}'
        assert ("New", "*", " Scenario MyScenario") in conn.calls

    def test_set_analysis_period(self) -> None:
        from atk.connect.scenario import ScenarioBuilder

        conn = MockATKConnection()
        builder = ScenarioBuilder(conn, "TestSc")
        builder.set_analysis_period("1 Jan 2024 00:00:00.000", "7 Jan 2024 00:00:00.000")

        assert ("SetAnalysisTimePeriod", "*", ' "1 Jan 2024 00:00:00.000" "7 Jan 2024 00:00:00.000"') in conn.calls

    def test_set_invalid_analysis_mode_raises(self) -> None:
        from atk.connect.scenario import ScenarioBuilder
        from atk import exceptions as atk_exc

        conn = MockATKConnection()
        builder = ScenarioBuilder(conn, "TestSc")

        with pytest.raises(atk_exc.ATKValueError, match="Invalid analysis mode"):
            builder.set_analysis_mode("NotARealMode")

    def test_save_with_path(self) -> None:
        from atk.connect.scenario import ScenarioBuilder

        conn = MockATKConnection()
        builder = ScenarioBuilder(conn, "TestSc")
        builder.save("C:/temp/test.xml")

        assert ("Save", "*/Scenario/TestSc", ' "C:/temp/test.xml"') in conn.calls

    def test_repr(self) -> None:
        from atk.connect.scenario import ScenarioBuilder

        conn = MockATKConnection()
        builder = ScenarioBuilder(conn, "MyScenario")
        assert "MyScenario" in repr(builder)
        assert "ScenarioBuilder" in repr(builder)
