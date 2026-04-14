"""
ATK Component 模式 — 报告导出

用 Python 风格的接口封装 ``IAtkObjectRoot.OutputDataReport()``。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from atk.component.session import ComponentSession


class ReportExporter:
    """
    从 ATK Component 模式导出数据报告。

    通过 :meth:`ComponentSession.report()
    <atk.component.session.ComponentSession.report>` 创建。

    示例::

        with component_session() as session:
            session.new_scenario('MyScenario')
            sat = session.create_satellite('Sat1')
            ...
            path = session.output_report(
                sat.satellite,
                'J2000 Position Velocity',
                '5 Nov 2022 00:00:00.000',
                '8 Nov 2022 00:00:00.000',
            )
            print(f"Report saved to: {path}")
    """

    def __init__(
        self,
        session: "ComponentSession",
        obj: Any,
        report_type: str,
        start: str,
        stop: str,
    ):
        self._session = session
        self._obj = obj
        self._report_type = report_type
        self._start = start
        self._stop = stop
        self._output_path: str | None = None

    def to_file(self, output_path: str) -> str:
        """
        生成报告并保存到文件。

        Parameters
        ----------
        output_path : str
            输出文件路径。

        Returns
        -------
        str
            ATK 输出文件路径。
        """
        result = self._session.root.OutputDataReport(
            self._obj,
            self._report_type,
            self._start,
            self._stop,
            output_path,
        )
        self._output_path = result
        return result

    def to_data(self) -> str:
        """
        生成报告并返回 ATK 默认输出路径。

        Returns
        -------
        str
            ATK 生成的输出文件路径。
        """
        result = self._session.root.OutputDataReport(
            self._obj,
            self._report_type,
            self._start,
            self._stop,
        )
        self._output_path = result
        return result

    @property
    def output_path(self) -> str | None:
        return self._output_path

    def __repr__(self) -> str:
        return (
            f"<ReportExporter type={self._report_type!r} "
            f"start={self._start!r} stop={self._stop!r}>"
        )
