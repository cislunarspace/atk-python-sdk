"""
ATK Connect Mode — MCS (Mission Control Sequence) Builder

Provides a fluent API for building Astrogator MCS segment sequences
via Connect commands.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from atk import exceptions as _ex
from atk import utils

if TYPE_CHECKING:
    from atk.connect.session import ATKConnection


# Segment type names used in ATK Connect commands
class McsBuilder:
    """
    Fluent builder for Astrogator MCS (Mission Control Sequence) segments
    in Connect mode.

    Created via ``atk.mcs_builder('*/Satellite/Sat1')``.

    Example::

        mcs = atk.mcs_builder('*/Satellite/Sat1')
        mcs.initial_state_keplerian(sma=6678, ecc=0, inc=28.5, raan=0, argp=0, ta=0)
        mcs.propagate_until('10 Jan 2024 12:00:00.000')
        mcs.impulsive_burn(dv=[0.5, 0, 0])
        mcs.run()
    """

    def __init__(self, conn: "ATKConnection", sat_path: str):
        self._conn = conn
        self._sat_path = utils.resolve_path(sat_path)
        self._seg_index = 0  # tracks the next segment index
        self._seg_paths: list[str] = []  # tracks each segment's full path

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _next_seg_path(self, seg_type: str) -> str:
        """
        Build and register the next segment's property path.

        Example path:
        ``*/Satellite/Sat1/MainSequence.SegmentList.Segment_0.Initial_State.InitialState.Keplerian``
        """
        idx = self._seg_index
        self._seg_index += 1
        # Segment list format: Segment_<index>.<SegmentType>.<SegmentType>
        base = (
            f"{self._sat_path}"
            f"/MainSequence.SegmentList"
            f".Segment_{idx}.{seg_type}"
        )
        self._seg_paths.append(base)
        return base

    def _set(self, seg_path: str, property_name: str, value: str) -> None:
        """Send a SetValue command for a segment property."""
        self._conn.send("SetValue", self._sat_path, f' "{seg_path}.{property_name}" {value}')

    def _set_str(self, seg_path: str, property_name: str, value: str) -> None:
        """Send a SetValue command with a string value (quoted)."""
        self._conn.send("SetValue", self._sat_path, f' "{seg_path}.{property_name}" "{value}"')

    # ------------------------------------------------------------------
    # Segment insertion — these create segments and configure them
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
        Add an InitialState segment with Keplerian elements.

        Parameters
        ----------
        sma, ecc, inc, raan, argp, ta : float
            Keplerian orbital elements (units as documented in ATK).
        epoch : str, optional
            Epoch time string.

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
        Add an InitialState segment with Cartesian elements.

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
        Add a Propagate segment that runs until a stop time.

        Parameters
        ----------
        stop_time : str
            Stop time string in ATK format (e.g. ``"10 Jan 2024 12:00:00.000"``).
        prop_time_step : float
            Propagation time step in seconds.

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
        Add a Propagate segment that runs for a given duration.

        Parameters
        ----------
        duration_seconds : float
            Duration in seconds.
        time_step : float
            Propagation time step in seconds.

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
        Add an ImpulsiveBurn segment (finite DV but modelled as instantaneous).

        Parameters
        ----------
        dv : tuple/list of 3 floats
            Delta-V components in km/s.
        burn_direction : str
            Burn direction keyword. Default ``" CartesianX"`` applies DV along
            the spacecraft X axis. Other options: ``" Velocity"``,
            ``" Radius"``, ``" AntiVelocity"``, etc.

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
        Add a TargetSequence segment pointing at another object's final state.

        Parameters
        ----------
        endpoint_path : str
            ATK path of the target endpoint (e.g. ``"*/Scenario/Sat2"``).
        tolerance : float
            Convergence tolerance for the differential corrector.

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
    # Run
    # ------------------------------------------------------------------

    def run(self) -> "McsBuilder":
        """
        Run the MCS for the satellite.

        Returns
        -------
        self
        """
        self._conn.send("RunMCS", self._sat_path, "")
        return self

    def apply_changes(self) -> "McsBuilder":
        """
        Apply all pending profile changes after a run.

        Returns
        -------
        self
        """
        self._conn.send("ApplyAllProfileChanges", self._sat_path, "")
        return self

    def reset_profiles(self) -> "McsBuilder":
        """
        Reset all MCS profiles to their initial state.

        Returns
        -------
        self
        """
        self._conn.send("ResetAllProfiles", self._sat_path, "")
        return self

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def get_segment_count(self) -> int:
        """Return the number of segments added so far."""
        return self._seg_index

    def __repr__(self) -> str:
        return f"<McsBuilder sat={self._sat_path!r} segments={self._seg_index}>"


# ---------------------------------------------------------------------------
# Helper to add mcs_builder() to ATKConnection
# ---------------------------------------------------------------------------

def _mcs_builder_factory(conn: "ATKConnection", sat_path: str) -> McsBuilder:
    return McsBuilder(conn, sat_path)


def _patch_connection():
    from atk.connect import session as _s

    def mcs_builder(self, sat_path: str) -> McsBuilder:
        """Create an McsBuilder for the given satellite path."""
        return _mcs_builder_factory(self, sat_path)

    _s.ATKConnection.mcs_builder = mcs_builder


_patch_connection()
del _patch_connection
