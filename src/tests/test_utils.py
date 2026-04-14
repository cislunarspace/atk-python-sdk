"""
atk.utils 的单元测试 — 时间解析、路径工具、结果解析。
"""

import pytest
from atk import utils
from atk import exceptions as atk_exc


class TestParseAtkTime:
    """parse_atk_time() 的测试。"""

    def test_full_datetime(self) -> None:
        dt = utils.parse_atk_time("5 Nov 2022 00:00:00.000")
        assert dt.year == 2022
        assert dt.month == 11
        assert dt.day == 5
        assert dt.hour == 0
        assert dt.minute == 0
        assert dt.second == 0

    def test_date_only(self) -> None:
        dt = utils.parse_atk_time("5 Nov 2022")
        assert dt.year == 2022
        assert dt.month == 11
        assert dt.day == 5

    def test_datetime_no_millis(self) -> None:
        dt = utils.parse_atk_time("5 Nov 2022 12:30:45")
        assert dt.hour == 12
        assert dt.minute == 30
        assert dt.second == 45

    def test_compact_iso_format(self) -> None:
        dt = utils.parse_atk_time("2022-11-05 12:30:45.123")
        assert dt.year == 2022
        assert dt.month == 11
        assert dt.day == 5
        assert dt.hour == 12
        assert dt.minute == 30
        assert dt.second == 45

    def test_empty_string_raises(self) -> None:
        with pytest.raises(atk_exc.ATKValueError):
            utils.parse_atk_time("")

    def test_unknown_format_raises(self) -> None:
        with pytest.raises(atk_exc.ATKValueError):
            utils.parse_atk_time("not a valid time")


class TestFormatAtkTime:
    """format_atk_time() 的测试。"""

    def test_roundtrip(self) -> None:
        from datetime import datetime
        original = datetime(2022, 11, 5, 12, 30, 45, 123000)
        result = utils.format_atk_time(original)
        assert "5 Nov 2022" in result
        assert "12:30:45" in result


class TestResolvePath:
    """resolve_path() 的测试。"""

    def test_already_wildcard(self) -> None:
        assert utils.resolve_path("*/Satellite/Sat1") == "*/Satellite/Sat1"

    def test_adds_wildcard(self) -> None:
        assert utils.resolve_path("Satellite/Sat1") == "*/Satellite/Sat1"

    def test_starts_with_slash(self) -> None:
        assert utils.resolve_path("/Satellite/Sat1") == "*/Satellite/Sat1"

    def test_asterisk_root(self) -> None:
        assert utils.resolve_path("*") == "*"


class TestPathHelpers:
    """path_join、path_parent、path_name 的测试。"""

    def test_path_join(self) -> None:
        assert utils.path_join("*", "Satellite", "Sat1") == "*/Satellite/Sat1"
        assert utils.path_join("*/Scenario/Sc1", "Satellite") == "*/Scenario/Sc1/Satellite"

    def test_path_name(self) -> None:
        assert utils.path_name("*/Satellite/Sat1") == "Sat1"
        assert utils.path_name("*/Constellation/Star") == "Star"

    def test_path_parent(self) -> None:
        assert utils.path_parent("*/Satellite/Sat1") == "*/Satellite"
        assert utils.path_parent("*/Satellite") == "*"


class TestValidateName:
    """validate_name() 的测试。"""

    def test_valid_name(self) -> None:
        assert utils.validate_name("Satellite1") == "Satellite1"
        assert utils.validate_name("My_Scenario_2024") == "My_Scenario_2024"

    def test_empty_raises(self) -> None:
        with pytest.raises(atk_exc.ATKValueError):
            utils.validate_name("")
        with pytest.raises(atk_exc.ATKValueError):
            utils.validate_name("   ")

    def test_invalid_characters_raises(self) -> None:
        with pytest.raises(atk_exc.ATKValueError):
            utils.validate_name("Sat/Sat1")
        with pytest.raises(atk_exc.ATKValueError):
            utils.validate_name("Sat*Sat")


class TestResultParsing:
    """CMDRESULT 解析辅助函数的测试。"""

    def test_result_to_list_with_string(self) -> None:
        class MockResult:
            m_vectData = "val1 val2 val3"

        result = MockResult()
        assert utils.result_to_list(result) == ["val1", "val2", "val3"]

    def test_result_to_list_with_list(self) -> None:
        class MockResult:
            m_vectData = ["val1", "val2"]

        result = MockResult()
        assert utils.result_to_list(result) == ["val1", "val2"]

    def test_result_to_list_none(self) -> None:
        assert utils.result_to_list(None) == []

    def test_result_to_dict_matching_lengths(self) -> None:
        class MockResult:
            m_vectData = "1.0 2.0 3.0"

        result = MockResult()
        d = utils.result_to_dict(result, ["x", "y", "z"])
        assert d == {"x": "1.0", "y": "2.0", "z": "3.0"}

    def test_result_to_dict_mismatched_lengths_raises(self) -> None:
        class MockResult:
            m_vectData = "1.0 2.0"

        result = MockResult()
        with pytest.raises(atk_exc.ATKValueError):
            utils.result_to_dict(result, ["x", "y", "z"])
