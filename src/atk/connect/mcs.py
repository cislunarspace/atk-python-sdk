"""
ATK Connect 模式 — MCS（任务控制序列）构建器

提供流式 API，通过 Connect 命令构建 Astrogator MCS 段序列。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from atk import exceptions as _ex
from atk import utils

if TYPE_CHECKING:
    from atk.connect.session import ATKConnection


class McsBuilder:
    """
    Connect 模式下 Astrogator MCS（任务控制序列）段的流式构建器。

    通过 ``atk.mcs_builder('*/Satellite/Sat1')`` 创建。

    示例::

        mcs = atk.mcs_builder('*/Satellite/Sat1')
        mcs.initial_state_keplerian(sma=6678, ecc=0, inc=28.5, raan=0, argp=0, ta=0)
        mcs.propagate_until('10 Jan 2024 12:00:00.000')
        mcs.impulsive_burn(dv=[0.5, 0, 0])
        mcs.run()
    """

    def __init__(self, conn: "ATKConnection", sat_path: str):
        self._conn = conn
        self._sat_path = utils.resolve_path(sat_path)
        self._seg_index = 0  # 跟踪下一个段的索引
        self._seg_paths: list[str] = []  # 跟踪每个段的完整路径

    # ------------------------------------------------------------------
    # 内部辅助方法
    # ------------------------------------------------------------------

    def _next_seg_path(self, seg_type: str) -> str:
        """
        构建并注册下一段的属性路径。

        示例路径：
        ``MainSequence.SegmentList.Segment_0.Initial_State.InitialState.Keplerian``
        """
        idx = self._seg_index
        self._seg_index += 1
        # 段列表格式：Segment_<index>.<SegmentType>.<SegmentType>
        # （相对于 sat_path，无前导斜杠）
        base = (
            f"MainSequence.SegmentList"
            f".Segment_{idx}.{seg_type}"
        )
        self._seg_paths.append(f"{self._sat_path}/{base}")
        return base

    def _set(self, seg_path: str, property_name: str, value: str) -> None:
        """发送段的属性的 SetValue 命令。"""
        self._conn.send("SetValue", self._sat_path, f' "{seg_path}.{property_name}" {value}')

    def _set_str(self, seg_path: str, property_name: str, value: str) -> None:
        """发送带引号字符串值的 SetValue 命令。"""
        self._conn.send("SetValue", self._sat_path, f' "{seg_path}.{property_name}" "{value}"')

    # ------------------------------------------------------------------
    # 段插入 — 创建段并配置
    # ------------------------------------------------------------------

    def initial_state_keplerian(
        self,
        sma: float,
        ecc: float,
        inc: float,
        raan: float,
        argp: float,
        ta: float,
        epoch: str | None = None,
    ) -> "McsBuilder":
        """
        添加一个带开普勒元素的 InitialState 段。

        Parameters
        ----------
        sma, ecc, inc, raan, argp, ta : float
            开普勒轨道元素（单位如 ATK 文档所述）。
        epoch : str, optional
            历元时间字符串。

        Returns
        -------
        self
        """
        seg = self._next_seg_path("Initial_State.InitialState.Keplerian")
        self._conn.send("InsertSegment", self._sat_path, f' Initial_State Segment_{self._seg_index - 1}')
        self._set(seg, "sma", str(sma))
        self._set(seg, "ecc", str(ecc))
        self._set(seg, "inc", str(inc))
        self._set(seg, "raan", str(raan))
        self._set(seg, "argp", str(argp))
        self._set(seg, "ta", str(ta))
        if epoch:
            self._set_str(seg, "epoch", epoch)
        return self

    def initial_state_cartesian(
        self,
        x: float, y: float, z: float,
        vx: float, vy: float, vz: float,
        epoch: str | None = None,
    ) -> "McsBuilder":
        """
        添加一个带笛卡尔坐标元素的 InitialState 段。

        Returns
        -------
        self
        """
        seg = self._next_seg_path("Initial_State.InitialState.Cartesian")
        self._conn.send("InsertSegment", self._sat_path, f' Initial_State Segment_{self._seg_index - 1}')
        self._set(seg, "CartesianX", str(x))
        self._set(seg, "CartesianY", str(y))
        self._set(seg, "CartesianZ", str(z))
        self._set(seg, "CartesianVX", str(vx))
        self._set(seg, "CartesianVY", str(vy))
        self._set(seg, "CartesianVZ", str(vz))
        if epoch:
            self._set_str(seg, "Epoch", epoch)
        return self

    def propagate_until(
        self,
        stop_time: str,
        prop_time_step: float = 60.0,
    ) -> "McsBuilder":
        """
        添加一个 Propagate 段，运行到指定的停止时间。

        Parameters
        ----------
        stop_time : str
            ATK 格式的停止时间字符串（如 ``"10 Jan 2024 12:00:00.000"``）。
        prop_time_step : float
            传播时间步长（秒）。

        Returns
        -------
        self
        """
        seg = self._next_seg_path("Propagate")
        idx = self._seg_index - 1
        self._conn.send("InsertSegment", self._sat_path, f' Propagate Segment_{idx}')
        self._set_str(seg, "StopTime", stop_time)
        self._set(seg, "TimeStep", str(prop_time_step))
        return self

    def propagate_duration(
        self,
        duration_seconds: float,
        time_step: float = 60.0,
    ) -> "McsBuilder":
        """
        添加一个 Propagate 段，运行指定的持续时间。

        Parameters
        ----------
        duration_seconds : float
            持续时间（秒）。
        time_step : float
            传播时间步长（秒）。

        Returns
        -------
        self
        """
        seg = self._next_seg_path("Propagate")
        idx = self._seg_index - 1
        self._conn.send("InsertSegment", self._sat_path, f' Propagate Segment_{idx}')
        self._set(seg, "Duration", str(duration_seconds))
        self._set(seg, "TimeStep", str(time_step))
        return self

    def impulsive_burn(
        self,
        dv: tuple[float, float, float] | list[float],
        burn_direction: str = " CartesianX",
    ) -> "McsBuilder":
        """
        添加一个 ImpulsiveBurn 段（有限 DV 但建模为瞬时的）。

        Parameters
        ----------
        dv : tuple/list，包含 3 个浮点数
            Delta-V 分量（km/s）。
        burn_direction : str
            点火方向关键字。默认 ``" CartesianX"`` 沿航天器 X 轴施加 DV。
            其他选项：``" Velocity"``、``" Radius"``、``" AntiVelocity"`` 等。

        Returns
        -------
        self
        """
        if len(dv) != 3:
            raise _ex.ATKValueError(f"dv must have 3 components, got {len(dv)}")
        seg = self._next_seg_path("ImpulsiveBurn")
        idx = self._seg_index - 1
        self._conn.send("InsertSegment", self._sat_path, f' ImpulsiveBurn Segment_{idx}')
        self._set(seg, "dvX", str(dv[0]))
        self._set(seg, "dvY", str(dv[1]))
        self._set(seg, "dvZ", str(dv[2]))
        self._set_str(seg, "Direction", burn_direction)
        return self

    def target_sequence(
        self,
        endpoint_path: str,
        tolerance: float = 1e-6,
    ) -> "McsBuilder":
        """
        添加一个 TargetSequence 段，指向另一个对象的最终状态。

        Parameters
        ----------
        endpoint_path : str
            目标端点的 ATK 路径（如 ``"*/Scenario/Sat2"``）。
        tolerance : float
            微分修正器的收敛容差。

        Returns
        -------
        self
        """
        seg = self._next_seg_path("TargetSequence")
        idx = self._seg_index - 1
        self._conn.send("InsertSegment", self._sat_path, f' TargetSequence Segment_{idx}')
        self._set_str(seg, "Endpoint", endpoint_path)
        self._set(seg, "Tolerance", str(tolerance))
        return self

    # ------------------------------------------------------------------
    # 运行
    # ------------------------------------------------------------------

    def run(self) -> "McsBuilder":
        """
        运行卫星的 MCS。

        Returns
        -------
        self
        """
        self._conn.send("RunMCS", self._sat_path, "")
        return self

    def apply_changes(self) -> "McsBuilder":
        """
        运行后应用所有待处理的配置变更。

        Returns
        -------
        self
        """
        self._conn.send("ApplyAllProfileChanges", self._sat_path, "")
        return self

    def reset_profiles(self) -> "McsBuilder":
        """
        将所有 MCS 配置重置为初始状态。

        Returns
        -------
        self
        """
        self._conn.send("ResetAllProfiles", self._sat_path, "")
        return self

    # ------------------------------------------------------------------
    # 查询
    # ------------------------------------------------------------------

    def get_segment_count(self) -> int:
        """返回目前已添加的段数量。"""
        return self._seg_index

    def __repr__(self) -> str:
        return f"<McsBuilder sat={self._sat_path!r} segments={self._seg_index}>"


# ---------------------------------------------------------------------------
# 将 mcs_builder() 添加到 ATKConnection 的辅助函数
# ---------------------------------------------------------------------------

def _mcs_builder_factory(conn: "ATKConnection", sat_path: str) -> McsBuilder:
    return McsBuilder(conn, sat_path)


def _patch_connection():
    from atk.connect import session as _s

    def mcs_builder(self, sat_path: str) -> McsBuilder:
        """为指定卫星路径创建 McsBuilder。"""
        return _mcs_builder_factory(self, sat_path)

    _s.ATKConnection.mcs_builder = mcs_builder


_patch_connection()
del _patch_connection
