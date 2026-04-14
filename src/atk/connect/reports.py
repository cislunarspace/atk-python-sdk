"""
ATK Connect Mode — Report Execution and Result Parsing

Provides wrappers for ATK report commands with parsed output
(converted to dict / pandas DataFrame).
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
    Parsed ATK report result.

    Attributes
    ----------
    raw : CMDRESULT
        The raw SWIG result object.
    data : list[str]
        Parsed row strings from ``m_vectData``.
    columns : list[str]
        Column headers (if available from the report style).
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
        Convert the report to a list of row dictionaries.

        Uses column headers as keys if available; otherwise uses ``col_0``,
        ``col_1``, ... as fallbacks.
        """
        cols = self.columns
        rows = self.data
        if not rows:
            return []

        # Reports are typically space-delimited with columns repeating
        # Try to group into rows of known width
        n_cols = len(cols) if cols else 0
        if n_cols == 0:
            # Fallback: single column, each item is a row
            return [{"value": v} for v in rows]

        result = []
        for i in range(0, len(rows), n_cols):
            chunk = rows[i : i + n_cols]
            if len(chunk) == n_cols:
                result.append(dict(zip(cols, chunk)))
            else:
                # Partial row at end
                result.append(dict(zip([f"col_{j}" for j in range(len(chunk))], chunk)))
        return result

    def to_dataframe(self) -> "pd.DataFrame":
        """
        Convert the report to a ``pandas.DataFrame``.

        Requires ``pandas`` to be installed.

        Returns
        -------
        DataFrame
        """
        try:
            import pandas as pd  # noqa: F401
        except ImportError:
            raise _ex.ATKReportError(
                "pandas is required for to_dataframe(). "
                "Install it with: pip install pandas"
            )

        import pandas as pd

        dicts = self.to_dict()
        if not dicts:
            return pd.DataFrame()
        return pd.DataFrame(dicts)

    def __repr__(self) -> str:
        count = len(self.data)
        return f"<ReportResult rows={count}>"


class QuickReport:
    """
    Execute a QuickReport-style command and return a parsed result.

    Created via :meth:`ATKConnection.quick_report()
    <atk.connect.session.ATKConnection.quick_report>`.

    Example::

        result = atk.quick_report('*/Satellite/Sat1', 'Position', time_period='*')
        df = result.to_dataframe()
    """

    # Known report styles and their column names
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
        Execute the report and return a parsed result.

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
    Execute a Report_RM (Report with file output) command.

    Example::

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
        Execute the report.

        Parameters
        ----------
        output_file : str, optional
            Output file path for the report. If None, result is returned
            as data rows.

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
# Add convenience methods to ATKConnection
# ---------------------------------------------------------------------------

def _patch_connection():
    from atk.connect import session as _s

    def quick_report(
        self,
        obj_path: str,
        style: str,
        time_period: str = "*",
    ) -> ReportResult:
        """Execute a quick report and return parsed results."""
        return QuickReport(self, obj_path, style, time_period).run()

    def report_rm(
        self,
        obj_path: str,
        style: str,
        time_period: str = "*",
    ) -> ReportResult:
        """Execute a Report_RM command and return parsed results."""
        return ReportRM(self, obj_path, style, time_period).run()

    _s.ATKConnection.quick_report = quick_report
    _s.ATKConnection.report_rm = report_rm


_patch_connection()
del _patch_connection
