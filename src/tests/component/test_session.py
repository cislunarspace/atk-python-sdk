"""
atk.component.session 的单元测试 — ComponentSession。

使用 unittest.mock 模拟 ATK Component SWIG 对象。
"""

import pytest
from unittest.mock import MagicMock, patch

from atk import exceptions as atk_exc


class TestComponentSessionNewScenario:
    """ComponentSession.new_scenario() 的测试。"""

    def test_new_scenario_returns_scenario_object(self):
        mock_atk = MagicMock()
        mock_root = MagicMock()
        mock_scenario = MagicMock()
        mock_root.NewScenario.return_value = None
        mock_root.GetCurrentScenario.return_value = mock_scenario
        mock_atk.IAtkObjectRoot.return_value = mock_root

        with patch("atk.component.session._find_component_module", return_value=mock_atk):
            # 强制重新导入以应用 patch
            import importlib
            import atk.component.session
            importlib.reload(atk.component.session)
            from atk.component.session import ComponentSession

            session = ComponentSession(mock_root)
            result = session.new_scenario("TestScenario")

            mock_root.NewScenario.assert_called_once_with("TestScenario")
            assert result is mock_scenario
            assert session.scenario is mock_scenario

    def test_new_scenario_raises_if_scenario_already_loaded(self):
        mock_atk = MagicMock()
        with patch("atk.component.session._find_component_module", return_value=mock_atk):
            import importlib
            import atk.component.session
            importlib.reload(atk.component.session)
            from atk.component.session import ComponentSession

            mock_root = MagicMock()
            session = ComponentSession(mock_root)
            session._scenario = MagicMock()  # 已加载场景

            with pytest.raises(atk_exc.ATKScenarioError, match="already loaded"):
                session.new_scenario("AnotherScenario")


class TestComponentSessionCreateSatellite:
    """ComponentSession.create_satellite() 的测试。"""

    def test_create_satellite_raises_without_scenario(self):
        mock_atk = MagicMock()
        with patch("atk.component.session._find_component_module", return_value=mock_atk):
            import importlib
            import atk.component.session
            importlib.reload(atk.component.session)
            from atk.component.session import ComponentSession

            mock_root = MagicMock()
            session = ComponentSession(mock_root)
            # 没有加载场景

            with pytest.raises(atk_exc.ATKScenarioError, match="Create a scenario first"):
                session.create_satellite("Sat1")

    def test_create_satellite_calls_new_on_children(self):
        mock_atk = MagicMock()
        mock_root = MagicMock()
        mock_scenario = MagicMock()
        mock_children = MagicMock()
        mock_sat = MagicMock()
        mock_root.GetCurrentScenario.return_value = mock_scenario
        mock_scenario.GetChildren.return_value = mock_children
        mock_children.New.return_value = mock_sat
        mock_atk.eSatellite = "eSatellite"

        with patch("atk.component.session._find_component_module", return_value=mock_atk):
            import importlib
            import atk.component.session
            importlib.reload(atk.component.session)
            from atk.component.session import ComponentSession

            session = ComponentSession(mock_root)
            session._scenario = mock_scenario

            result = session.create_satellite("Sat1")

            mock_children.New.assert_called_once()
            assert result is mock_sat
