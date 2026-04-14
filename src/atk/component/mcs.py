"""
ATK Component Mode — MCS (Mission Control Sequence) Builder

Provides a fluent API for building Astrogator MCS segment sequences
using the SWIG-wrapped IVADriverMCS / IVAMCSSegmentCollection.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from atk import exceptions as _ex
if TYPE_CHECKING:
    from atk.component.satellite import SatelliteBuilder


# Segment type names used in ATK Component API
class McsBuilder:
    """
    Fluent builder for Astrogator MCS segments in Component mode.

    Created via :meth:`SatelliteBuilder.get_mcs_driver()
    <atk.component.satellite.SatelliteBuilder.get_mcs_driver>` to get
    a driver, then call :meth:`driver.main_sequence()
    <IVADriverMCS.main_sequence>` to get a builder, or instantiate this
    class directly::

        sat = scenario.create_satellite('Sat1')
        sat.set_propagator_type('PropagatorAstromaster')
        mcs = McsBuilder(sat)
        mcs.initial_state_keplerian(sma=6678, ecc=0, inc=28.5, ...)
        mcs.propagate_until('10 Jan 2024 12:00:00')
        mcs.run()

    Attributes
    ----------
    driver : IVADriverMCS
        The MCS driver obtained from the satellite.
    """

    def __init__(self, sat_or_driver: Any):
        """
        Parameters
        ----------
        sat_or_driver : ISatellite or IVADriverMCS
            The satellite or its already-obtained propagator driver.
        """
        # Accept either ISatellite or IVADriverMCS
        self._driver: Any = None
        self._seq: Any = None
        self._seg_count = 0

        if hasattr(sat_or_driver, "GetPropagator"):
            # It's an ISatellite
            self._driver = sat_or_driver.GetPropagator()
        elif hasattr(sat_or_driver, "GetMainSequence"):
            # It's already an IVADriverMCS
            self._driver = sat_or_driver
        else:
            raise _ex.ATKMCSError(
                f"Expected ISatellite or IVADriverMCS, got {type(sat_or_driver).__name__}"
            )

        self._seq = self._driver.GetMainSequence()
        self._seg_count = self._seq.GetCount() if self._seq else 0

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def driver(self) -> Any:
        return self._driver

    @property
    def segment_count(self) -> int:
        """Number of segments currently in the sequence."""
        return self._seg_count

    # ------------------------------------------------------------------
    # Segment builders
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

        Returns
        -------
        self
        """
        seg = self._append_segment("Initial_State")
        props = seg.GetProperties()
        _set_prop(props, "sma", sma)
        _set_prop(props, "ecc", ecc)
        _set_prop(props, "inc", inc)
        _set_prop(props, "raan", raan)
        _set_prop(props, "argp", argp)
        _set_prop(props, "ta", ta)
        if epoch:
            _set_prop(props, "epoch", epoch)
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
        seg = self._append_segment("Initial_State")
        props = seg.GetProperties()
        _set_prop(props, "CartesianX", x)
        _set_prop(props, "CartesianY", y)
        _set_prop(props, "CartesianZ", z)
        _set_prop(props, "CartesianVX", vx)
        _set_prop(props, "CartesianVY", vy)
        _set_prop(props, "CartesianVZ", vz)
        if epoch:
            _set_prop(props, "Epoch", epoch)
        return self

    def propagate_until(
        self,
        stop_time: str,
        time_step: float = 60.0,
    ) -> "McsBuilder":
        """
        Add a Propagate segment.

        Parameters
        ----------
        stop_time : str
            Stop time in ATK format.
        time_step : float
            Propagation time step in seconds.

        Returns
        -------
        self
        """
        seg = self._append_segment("Propagate")
        props = seg.GetProperties()
        _set_prop(props, "StopTime", stop_time)
        _set_prop(props, "TimeStep", time_step)
        return self

    def propagate_duration(
        self,
        duration_seconds: float,
        time_step: float = 60.0,
    ) -> "McsBuilder":
        """
        Add a Propagate segment for a given duration.

        Returns
        -------
        self
        """
        seg = self._append_segment("Propagate")
        props = seg.GetProperties()
        _set_prop(props, "Duration", duration_seconds)
        _set_prop(props, "TimeStep", time_step)
        return self

    def impulsive_burn(
        self,
        dv: tuple[float, float, float] | list[float],
        direction: str = "CartesianX",
    ) -> "McsBuilder":
        """
        Add an ImpulsiveBurn segment.

        Parameters
        ----------
        dv : tuple/list of 3 floats
            Delta-V components.
        direction : str
            Burn direction. Default ``"CartesianX"``.

        Returns
        -------
        self
        """
        if len(dv) != 3:
            raise _ex.ATKValueError(f"dv must have 3 components, got {len(dv)}")
        seg = self._append_segment("ImpulsiveBurn")
        props = seg.GetProperties()
        _set_prop(props, "dvX", dv[0])
        _set_prop(props, "dvY", dv[1])
        _set_prop(props, "dvZ", dv[2])
        _set_prop(props, "Direction", direction)
        return self

    def target_sequence(
        self,
        endpoint_path: str,
        tolerance: float = 1e-6,
    ) -> "McsBuilder":
        """
        Add a TargetSequence segment.

        Returns
        -------
        self
        """
        seg = self._append_segment("TargetSequence")
        props = seg.GetProperties()
        _set_prop(props, "Endpoint", endpoint_path)
        _set_prop(props, "Tolerance", tolerance)
        return self

    # ------------------------------------------------------------------
    # Run / apply
    # ------------------------------------------------------------------

    def run(self) -> "McsBuilder":
        """Run the MCS."""
        self._driver.RunMCS()
        return self

    def apply_changes(self) -> "McsBuilder":
        """Apply all pending profile changes."""
        self._driver.ApplyAllProfileChanges()
        return self

    def reset_profiles(self) -> "McsBuilder":
        """Reset all profiles to their initial state."""
        self._driver.ResetAllProfiles()
        return self

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _append_segment(self, seg_type: str) -> Any:
        """
        Append a new segment of the given type to the main sequence.

        Returns the newly created segment object.
        """
        # IVAMCSSegmentCollection.AppendSegment(type_name)
        seg = self._seq.AppendSegment(seg_type)
        self._seg_count += 1
        return seg

    def __repr__(self) -> str:
        return f"<McsBuilder segments={self._seg_count}>"


# ---------------------------------------------------------------------------
# Internal property setter helper
# ---------------------------------------------------------------------------

def _set_prop(props: Any, name: str, value: float | str) -> None:
    """
    Set a property on an MCS segment properties object.

    Tries SetValue first, then SetXxx(name) setter pattern.
    """
    if hasattr(props, "SetValue"):
        props.SetValue(name, value)
    else:
        # Try SetXxx pattern
        setter = getattr(type(props), f"Set{name}", None)
        if setter:
            setter(props, value)
        else:
            raise _ex.ATKMCSError(
                f"Cannot set property {name!r} on segment properties. "
                f"Available methods: {[m for m in dir(props) if m.startswith('Set')]}"
            )
