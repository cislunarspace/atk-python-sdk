"""
ATK Connect 模式 — 报告执行与结果解析

提供 ATK 报告命令的封装，支持解析输出
（转换为 dict / pandas DataFrame）。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from atk import exceptions as _ex
from atk import utils

if TYPE_CHECKING:
    import pandas as pd
    from atk.connect.session import ATKConnection


class ReportResult:
    """
    解析后的 ATK 报告结果。

    Attributes
    ----------
    raw : CMDRESULT
        原始 SWIG 结果对象。
    data : list[str]
        从 ``m_vectData`` 解析的行字符串。
    columns : list[str]
        列标题（如果报告样式可用）。
    """

    def __init__(
        self,
        raw,
        columns: list[str] | None = None,
    ):
        self.raw = raw
        self._data: list[str] | None = None
        self._columns = columns

    @property
    def data(self) -> list[str]:
        if self._data is None:
            self._data = utils.result_to_list(self.raw)
        return self._data

    @property
    def columns(self) -> list[str]:
        if self._columns is None:
            self._columns = []
        return self._columns

    def to_dict(self) -> list[dict[str, str]]:
        """
        将报告转换为行字典列表。

        如果有列标题则用作键；否则使用 ``col_0``、``col_1`` ... 作为回退。
        """
        cols = self.columns
        rows = self.data
        if not rows:
            return []

        # 报告通常以空格分隔，列会重复
        # 尝试按已知宽度分组为行
        n_cols = len(cols) if cols else 0
        if n_cols == 0:
            # 回退：单列，每个项为一行
            return [{"value": v} for v in rows]

        result = []
        for i in range(0, len(rows), n_cols):
            chunk = rows[i : i + n_cols]
            if len(chunk) == n_cols:
                result.append(dict(zip(cols, chunk)))
            else:
                # 末尾不完整的行
                result.append(dict(zip([f"col_{j}" for j in range(len(chunk))], chunk)))
        return result

    def to_dataframe(self) -> "pd.DataFrame":
        """
        将报告转换为 ``pandas.DataFrame``。

        需要安装 ``pandas``。

        Returns
        -------
        DataFrame
        """
        try:
            import pandas as pd
        except ImportError:
            raise _ex.ATKReportError(
                "pandas is required for to_dataframe(). "
                "Install it with: pip install pandas"
            )

        dicts = self.to_dict()
        if not dicts:
            return pd.DataFrame()
        return pd.DataFrame(dicts)

    def __repr__(self) -> str:
        count = len(self.data)
        return f"<ReportResult rows={count}>"


class QuickReport:
    """
    执行 QuickReport 样式的命令并返回解析结果。

    通过 :meth:`ATKConnection.quick_report()
    <atk.connect.session.ATKConnection.quick_report>` 创建。

    示例::

        result = atk.quick_report('*/Satellite/Sat1', 'Position', time_period='*')
        df = result.to_dataframe()
    """

    # 已知的报告样式及其列名
    _REPORT_COLUMNS = {
        "Position":         ["time", "x", "y", "z", "vx", "vy", "vz"],
        "Keplerian":        ["time", "sma", "ecc", "inc", "raan", "argp", "ta"],
        "J2000Position":    ["time", "x", "y", "z"],
        "J2000PositionVelocity": ["time", "x", "y", "z", "vx", "vy", "vz"],
        "LLA":              ["time", "lat", "lon", "alt"],
        "Access":          ["time", "access"],
        "AER":             ["time", "az", "el", "range"],
    }

    def __init__(
        self,
        conn: "ATKConnection",
        obj_path: str,
        style: str,
        time_period: str = "*",
    ):
        self._conn = conn
        self._obj_path = utils.resolve_path(obj_path)
        self._style = style
        self._time_period = time_period

    def run(self) -> ReportResult:
        """
        执行报告并返回解析结果。

        Returns
        -------
        ReportResult
        """
        style_key = self._style.replace(" ", "")
        columns = self._REPORT_COLUMNS.get(self._style, [])

        raw = self._conn.send(
            f"QuickReport_{style_key}",
            self._obj_path,
            f" {self._time_period}",
        )
        return ReportResult(raw, columns=columns)


class ReportRM:
    """
    执行 Report_RM（带文件输出的报告）命令。

    示例::

        result = atk.report_rm(
            '*/Satellite/Sat1',
            style='J2000PositionVelocity',
            time_period='5 Nov 2022 00:00:00.000 8 Nov 2022 00:00:00.000'
        )
    """

    def __init__(
        self,
        conn: "ATKConnection",
        obj_path: str,
        style: str,
        time_period: str = "*",
    ):
        self._conn = conn
        self._obj_path = utils.resolve_path(obj_path)
        self._style = style
        self._time_period = time_period

    def run(
        self,
        output_file: str | None = None,
    ) -> ReportResult:
        """
        执行报告。

        Parameters
        ----------
        output_file : str, optional
            报告的输出文件路径。如果为 None，结果以数据行返回。

        Returns
        -------
        ReportResult
        """
        param = f' "{self._style}" {self._time_period}'
        if output_file:
            param += f' "{output_file}"'

        columns = QuickReport._REPORT_COLUMNS.get(self._style, [])
        raw = self._conn.send("Report_RM", self._obj_path, param)
        return ReportResult(raw, columns=columns)


# ---------------------------------------------------------------------------
# 为 ATKConnection 添加便捷方法
# ---------------------------------------------------------------------------

def _patch_connection():
    from atk.connect import session as _s

    def quick_report(
        self,
        obj_path: str,
        style: str,
        time_period: str = "*",
    ) -> ReportResult:
        """执行快速报告并返回解析结果。"""
        return QuickReport(self, obj_path, style, time_period).run()

    def report_rm(
        self,
        obj_path: str,
        style: str,
        time_period: str = "*",
    ) -> ReportResult:
        """执行 Report_RM 命令并返回解析结果。"""
        return ReportRM(self, obj_path, style, time_period).run()

    _s.ATKConnection.quick_report = quick_report
    _s.ATKConnection.report_rm = report_rm


_patch_connection()
del _patch_connection
