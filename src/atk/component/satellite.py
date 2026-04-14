"""
ATK Component Mode — Satellite Builder

Wraps ``ISatellite`` and ``IVADriverMCS`` with a Pythonic fluent API.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from atk import exceptions as _ex
from atk.component import session as _s

if TYPE_CHECKING:
    from atk.component.scenario import ScenarioBuilder


# Propagator string name → SWIG enum
_PROPAGATOR_MAP = {
    "PropagatorTwoBody":        "ePropagatorTwoBody",
    "PropagatorJ2Perturbation": "ePropagatorJ2Perturbation",
    "PropagatorHPOP":          "ePropagatorHPOP",
    "PropagatorSGP4":          "ePropagatorSGP4",
    "PropagatorStkExternal":   "ePropagatorStkExternal",
    "PropagatorAstromaster":   "ePropagatorAstromaster",
    "PropagatorGreatArc":      "ePropagatorGreatArc",
    "PropagatorSimpleAscent":   "ePropagatorSimpleAscent",
    "PropagatorJ4Perturbation": "ePropagatorJ4Perturbation",
    "PropagatorVinti":         "ePropagatorVinti",
    "PropagatorBallistic":     "ePropagatorBallistic",
}


class SatelliteBuilder:
    """
    Pythonic wrapper around ATK's ``ISatellite`` (Component mode).

    Created via :meth:`ScenarioBuilder.create_satellite() <atk.component.scenario.ScenarioBuilder.create_satellite>`.

    Example::

        sat = scenario.create_satellite('Sat1')
        sat.set_propagator_type('PropagatorAstromaster')
        sat.set_keplerian(sma=7100, ecc=0.001, inc=30, raan=0, argp=0, ta=0)
        mcs = sat.get_mcs_driver()
        ...
    """

    def __init__(self, sat: Any):
        self._sat = sat
        self._driver: Any | None = None

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        return self._sat.GetInstanceName()

    @property
    def path(self) -> str:
        return self._sat.GetPath()

    @property
    def satellite(self) -> Any:
        """Return the raw ``ISatellite`` SWIG object."""
        return self._sat

    # ------------------------------------------------------------------
    # Propagator configuration
    # ------------------------------------------------------------------

    def set_propagator_type(self, propagator: str | Any) -> "SatelliteBuilder":
        """
        Set the propagator type.

        Parameters
        ----------
        propagator : str
            Propagator name (e.g. ``"PropagatorAstromaster"``).
            Or the raw SWIG enum value.
        """
        if isinstance(propagator, str):
            enum_name = _PROPAGATOR_MAP.get(propagator)
            if enum_name is None:
                raise _ex.ATKValueError(
                    f"Unknown propagator {propagator!r}. "
                    f"Valid names: {list(_PROPAGATOR_MAP)}"
                )
            enum = getattr(_s._ATK, enum_name)
        else:
            enum = propagator

        self._sat.SetPropagatorType(enum)
        self._driver = None  # reset driver cache
        return self

    def get_mcs_driver(self) -> Any:
        """
        Get the MCS (Mission Control Sequence) driver for this satellite.

        Returns
        -------
        IVADriverMCS
        """
        if self._driver is None:
            self._driver = self._sat.GetPropagator()
        return self._driver

    # ------------------------------------------------------------------
    # Orbital state
    # ------------------------------------------------------------------

    def set_keplerian(
        self,
        sma: float,
        ecc: float,
        inc: float,
        raan: float,
        argp: float,
        ta: float,
        epoch: str | None = None,
    ) -> "SatelliteBuilder":
        """
        Set orbital state via Keplerian elements through the MCS driver.

        Note: This method accesses the MCS InitialState segment properties.
        The satellite must have a propagator set first.

        Parameters
        ----------
        sma : float
            Semi-major axis (km).
        ecc : float
            Eccentricity.
        inc : float
            Inclination (degrees).
        raan : float
            Right ascension of ascending node (degrees).
        argp : float
            Argument of periapsis (degrees).
        ta : float
            True anomaly (degrees).
        epoch : str, optional
            Epoch time string.

        Returns
        -------
        self
        """
        driver = self.get_mcs_driver()
        seq = driver.GetMainSequence()
        seg_count = seq.GetCount()
        if seg_count == 0:
            raise _ex.ATKSatelliteError(
                "MCS has no segments. "
                "Use McsBuilder to build the segment sequence before setting state."
            )

        # Walk the segment tree to find the InitialState segment
        # The first segment is typically the InitialState segment
        seg = _find_initial_state_segment(seq)
        if seg is None:
            raise _ex.ATKSatelliteError("Could not find InitialState segment in MCS.")

        props = seg.GetProperties()
        if props is None:
            raise _ex.ATKSatelliteError("InitialState segment has no properties.")

        _set_segment_property(props, "sma", sma)
        _set_segment_property(props, "ecc", ecc)
        _set_segment_property(props, "inc", inc)
        _set_segment_property(props, "raan", raan)
        _set_segment_property(props, "argp", argp)
        _set_segment_property(props, "ta", ta)
        if epoch:
            _set_segment_property(props, "epoch", epoch)

        return self

    def set_cartesian(
        self,
        x: float,
        y: float,
        z: float,
        vx: float,
        vy: float,
        vz: float,
        epoch: str | None = None,
    ) -> "SatelliteBuilder":
        """
        Set orbital state via Cartesian elements.

        Returns
        -------
        self
        """
        # Similar to set_keplerian but sets CartesianX/Y/Z/VX/VY/VZ
        driver = self.get_mcs_driver()
        seq = driver.GetMainSequence()
        seg = _find_initial_state_segment(seq)
        if seg is None:
            raise _ex.ATKSatelliteError("Could not find InitialState segment in MCS.")
        props = seg.GetProperties()
        _set_segment_property(props, "CartesianX", x)
        _set_segment_property(props, "CartesianY", y)
        _set_segment_property(props, "CartesianZ", z)
        _set_segment_property(props, "CartesianVX", vx)
        _set_segment_property(props, "CartesianVY", vy)
        _set_segment_property(props, "CartesianVZ", vz)
        if epoch:
            _set_segment_property(props, "Epoch", epoch)
        return self

    # ------------------------------------------------------------------
    # Mass properties
    # ------------------------------------------------------------------

    def set_mass(self, total_mass: float) -> "SatelliteBuilder":
        """
        Set the satellite's total mass (kg).

        Returns
        -------
        self
        """
        mp = self._sat.GetMassProperties()
        mp.SetTotalMass(total_mass)
        return self

    def set_stage_mass(
        self,
        dry_mass: float,
        wet_mass: float,
    ) -> "SatelliteBuilder":
        """
        Set dry and wet mass for stage modeling.

        Returns
        -------
        self
        """
        mp = self._sat.GetMassProperties()
        mp.SetDryMass(dry_mass)
        mp.SetPropellantMass(wet_mass - dry_mass)
        return self

    # ------------------------------------------------------------------
    # Attitude
    # ------------------------------------------------------------------

    def set_attitude_type(self, attitude_type: str | Any) -> "SatelliteBuilder":
        """
        Set the satellite's attitude type.

        Parameters
        ----------
        attitude_type : str
            Attitude type name (e.g. ``"CBF"``, ``"J2000"``).
            Or the raw SWIG enum value.
        """
        if isinstance(attitude_type, str):
            enum_name = f"eAttitude{attitude_type.capitalize()}"
            enum = getattr(_s._ATK, enum_name, None)
            if enum is None:
                raise _ex.ATKValueError(f"Unknown attitude type: {attitude_type!r}")
        else:
            enum = attitude_type

        self._sat.SetAttitudeType(enum)
        return self

    # ------------------------------------------------------------------
    # Graphics
    # ------------------------------------------------------------------

    def set_color(self, color_index: int) -> "SatelliteBuilder":
        """
        Set the satellite's graphics color by ATK color index.

        Returns
        -------
        self
        """
        gfx = self._sat.GetGraphics()
        gfx.SetColor(color_index)
        return self

    # ------------------------------------------------------------------
    # String representation
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"<SatelliteBuilder name={self.name!r}>"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _find_initial_state_segment(seq: Any) -> Any | None:
    """
    Walk the MCS segment collection to find the InitialState segment.

    Returns the segment or None if not found.
    """
    for i in range(seq.GetCount()):
        seg = seq.Item(i)
        seg_type = seg.GetType() if hasattr(seg, "GetType") else ""
        # Type is typically a string or enum — check for "InitialState"
        type_str = str(seg_type)
        if "InitialState" in type_str or "Initial" in type_str:
            return seg
    return None


def _set_segment_property(props: Any, name: str, value: float | str) -> None:
    """
    Set a named property on an MCS segment properties object.

    Uses the SetValue / SetProperty pattern observed in ATK Component API.
    """
    if hasattr(props, "SetValue"):
        props.SetValue(name, value)
    elif hasattr(props, f"Set{name}"):
        getattr(props, f"Set{name}")(value)
    else:
        # Last resort — try SetXxx pattern
        setter = getattr(props, f"Set{name}", None)
        if setter:
            setter(value)
        else:
            raise _ex.ATKMCSError(
                f"Segment properties object has no setter for {name!r}. "
                f"Available: {[a for a in dir(props) if a.startswith('Set')]}"
            )
