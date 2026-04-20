"""
atk.connect.coverage 的单元测试 — CoverageBuilder 和 CoverageStats。
"""

import pytest
from unittest.mock import MagicMock

from atk import exceptions as atk_exc


class TestCoverageStats:
    """CoverageStats 的测试。"""

    def test_unexpected_format_raises(self):
        from atk.connect.coverage import CoverageStats

        mock_raw = MagicMock()
        mock_raw.m_vectData = "completely unexpected format without equals signs"

        with pytest.raises(atk_exc.ATKError, match="Unexpected CoverageStats format"):
            _ = CoverageStats(mock_raw)

    def test_valid_key_value_format(self):
        from atk.connect.coverage import CoverageStats

        mock_raw = MagicMock()
        mock_raw.m_vectData = ["AccessCount=5", "TotalAccessTime=120.5", "MeanAccessDuration=24.1"]

        stats = CoverageStats(mock_raw)
        assert stats.access_count == 5
        assert stats.total_access_time == 120.5
        assert stats.mean_access_duration == 24.1

    def test_valid_positional_format(self):
        from atk.connect.coverage import CoverageStats

        mock_raw = MagicMock()
        mock_raw.m_vectData = ["10", "300.0", "30.0"]

        stats = CoverageStats(mock_raw)
        assert stats.access_count == 10
        assert stats.total_access_time == 300.0
        assert stats.mean_access_duration == 30.0
