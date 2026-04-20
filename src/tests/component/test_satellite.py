"""
atk.component.satellite 的单元测试 — SatelliteBuilder。

使用 unittest.mock 模拟 ISatellite SWIG 对象。
"""

import pytest
from unittest.mock import MagicMock, patch

from atk import exceptions as atk_exc


class TestSatelliteBuilderComponent:
    """Component mode SatelliteBuilder 的测试。"""

    def test_set_keplerian_calls_setvalue(self):
        """set_keplerian calls SetValue on segment properties."""
        mock_atk = MagicMock()
        mock_atk.ePropagatorTwoBody = "ePropagatorTwoBody"

        with patch("atk.component.session._find_component_module", return_value=mock_atk):
            import importlib
            import atk.component.session
            importlib.reload(atk.component.session)
            import atk.component.satellite
            importlib.reload(atk.component.satellite)
            from atk.component.satellite import SatelliteBuilder

            # 设置完整的 MCS 链
            mock_props = MagicMock()
            mock_seg = MagicMock()
            mock_seg.GetProperties.return_value = mock_props
            mock_seg.GetType.return_value = "InitialState"

            mock_seq = MagicMock()
            mock_seq.GetCount.return_value = 1
            mock_seq.Item.return_value = mock_seg

            mock_driver = MagicMock()
            mock_driver.GetMainSequence.return_value = mock_seq

            mock_sat = MagicMock()
            mock_sat.GetPropagator.return_value = mock_driver
            mock_sat.SetPropagatorType = MagicMock()

            builder = SatelliteBuilder(mock_sat)
            builder.set_keplerian(sma=6678, ecc=0, inc=28.5, raan=0, argp=0, ta=0)

            # 验证 SetValue 被调用
            mock_props.SetValue.assert_called()
            call_str = str(mock_props.SetValue.call_args_list)
            assert "sma" in call_str
            assert "ecc" in call_str
            assert "inc" in call_str

    def test_set_mass_calls_settotalmass(self):
        """set_mass calls SetTotalMass on mass properties."""
        mock_atk = MagicMock()
        with patch("atk.component.session._find_component_module", return_value=mock_atk):
            import importlib
            import atk.component.session
            importlib.reload(atk.component.session)
            import atk.component.satellite
            importlib.reload(atk.component.satellite)
            from atk.component.satellite import SatelliteBuilder

            mock_mp = MagicMock()
            mock_sat = MagicMock()
            mock_sat.GetMassProperties.return_value = mock_mp

            builder = SatelliteBuilder(mock_sat)
            builder.set_mass(500)

            mock_mp.SetTotalMass.assert_called_once_with(500)
