"""
atk.connect.scenario 的单元测试 — ScenarioBuilder。
"""

import pytest
from unittest.mock import MagicMock, patch

from tests.connect.conftest import MockATKConnection


class TestScenarioBuilder:
    """ScenarioBuilder 的测试。"""

    def test_create_scenario(self) -> None:
        from atk.connect.scenario import ScenarioBuilder

        conn = MockATKConnection()
        builder = ScenarioBuilder(conn, "MyScenario")
        builder.create()

        # ATK 格式：obj='/', param=' Scenario {name}'
        # 合并后：'/ Scenario {name}'
        assert ("New", "/", " Scenario MyScenario") in conn.calls

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

        assert ("SaveAs", "/", ' * "C:/temp/test.xml"') in conn.calls

    def test_save_without_path(self) -> None:
        from atk.connect.scenario import ScenarioBuilder

        conn = MockATKConnection()
        builder = ScenarioBuilder(conn, "TestSc")
        builder.save()

        assert ("Save", "/", " *") in conn.calls

    def test_repr(self) -> None:
        from atk.connect.scenario import ScenarioBuilder

        conn = MockATKConnection()
        builder = ScenarioBuilder(conn, "MyScenario")
        assert "MyScenario" in repr(builder)
        assert "ScenarioBuilder" in repr(builder)
