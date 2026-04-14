"""
ATK Connect Mode — Satellite Builder

Provides a fluent Python API for creating and configuring satellites
via Connect commands.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from atk import exceptions as _ex
from atk import utils

if TYPE_CHECKING:
    from atk.connect.session import ATKConnection


# ---------------------------------------------------------------------------
# Propagator type map — Connect command strings → ATK propagator names
# ---------------------------------------------------------------------------
_PROPAGATOR_CMD_MAP = {
    "PropagatorTwoBody":        "TwoBody",
    "PropagatorJ2Perturbation": "J2Perturbation",
    "PropagatorHPOP":          "HPOP",
    "PropagatorSGP4":          "SGP4",
    "PropagatorStkExternal":   "STKExternal",
    "PropagatorAstromaster":   "Astromaster",
    "PropagatorGreatArc":      "GreatArc",
    "PropagatorSimpleAscent":   "SimpleAscent",
    "PropagatorJ4Perturbation": "J4Perturbation",
    "PropagatorVinti":         "Vinti",
    "PropagatorBallistic":     "Ballistic",
}


class SatelliteBuilder:
    """
    Fluent builder for ATK satellites in Connect mode.

    Created via :meth:`ATKConnection.create_satellite() <atk.connect.session.ATKConnection.create_satellite>`.

    Example::

        sat = atk.create_satellite('Sat1')
        sat.set_propagator('PropagatorAstromaster')
        sat.set_keplerian(sma=7100, ecc=0.001, inc=30, raan=0, argp=0, ta=0)
        sat.set_mass(500)
        sat.propagate(duration_days=1)
    """

    def __init__(
        self,
        conn: "ATKConnection",
        name: str,
        scenario_path: str = "*",
    ):
        self._conn = conn
        self._name = utils.validate_name(name)
        self._scenario_path = scenario_path
        # Full ATK path to this satellite
        self._path = f"{utils.resolve_path(scenario_path)}/Satellite/{self._name}"
        self._propagator: str | None = None

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        return self._name

    @property
    def path(self) -> str:
        return self._path

    @property
    def propagator(self) -> str | None:
        return self._propagator

    # ------------------------------------------------------------------
    # Creation
    # ------------------------------------------------------------------

    def create(self) -> "SatelliteBuilder":
        """Create the satellite object in ATK."""
        self._conn.send("New", self._path, "")
        return self

    # ------------------------------------------------------------------
    # Propagator configuration
    # ------------------------------------------------------------------

    def set_propagator(self, propagator: str) -> "SatelliteBuilder":
        """
        Set the satellite's propagator type.

        Parameters
        ----------
        propagator : str
            Propagator name. Valid names:
            ``PropagatorTwoBody``, ``PropagatorJ2Perturbation``,
            ``PropagatorHPOP``, ``PropagatorSGP4``, ``PropagatorStkExternal``,
            ``PropagatorAstromaster``, ``PropagatorGreatArc``,
            ``PropagatorSimpleAscent``, ``PropagatorJ4Perturbation``,
            ``PropagatorVinti``, ``PropagatorBallistic``.
        """
        if propagator not in _PROPAGATOR_CMD_MAP:
            raise _ex.ATKValueError(
                f"Unknown propagator {propagator!r}. "
                f"Valid names: {list(_PROPAGATOR_CMD_MAP)}"
            )
        self._propagator = propagator
        cmd_name = _PROPAGATOR_CMD_MAP[propagator]
        self._conn.send("SetPropagator", self._path, f' "{cmd_name}"')
        return self

    # ------------------------------------------------------------------
    # Orbital state — Keplerian elements
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
        Set the satellite's orbital state using Keplerian elements.

        Parameters
        ----------
        sma : float
            Semi-major axis (km). Positive for orbit, negative for hyperbolic.
        ecc : float
            Eccentricity (0 ≤ ecc < 1 for elliptical).
        inc : float
            Inclination (degrees).
        raan : float
            Right ascension of ascending node (degrees).
        argp : float
            Argument of periapsis (degrees).
        ta : float
            True anomaly (degrees).
        epoch : str, optional
            Epoch time string in ATK format.

        Returns
        -------
        self
        """
        # The Connect path for Keplerian state in Astromaster MCS:
        # MainSequence.SegmentList.Initial_State.InitialState.Keplerian.sma
        base = f"{self._path}/MainSequence.SegmentList.Initial_State.InitialState.Keplerian"
        self._conn.send("SetValue", self._path, f' "{base}.sma" {sma}')
        self._conn.send("SetValue", self._path, f' "{base}.ecc" {ecc}')
        self._conn.send("SetValue", self._path, f' "{base}.inc" {inc}')
        self._conn.send("SetValue", self._path, f' "{base}.raan" {raan}')
        self._conn.send("SetValue", self._path, f' "{base}.argp" {argp}')
        self._conn.send("SetValue", self._path, f' "{base}.ta" {ta}')
        if epoch:
            self._conn.send("SetValue", self._path, f' "{base}.epoch" "{epoch}"')
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
        Set the satellite's orbital state using Cartesian elements.

        Parameters
        ----------
        x, y, z : float
            Position components (km) in the specified frame.
        vx, vy, vz : float
            Velocity components (km/s) in the specified frame.
        epoch : str, optional
            Epoch time string in ATK format.
        frame : str
            Coordinate frame name (e.g. ``"J2000"``, ``"ECF"``).

        Returns
        -------
        self
        """
        base = f"{self._path}/MainSequence.SegmentList.Initial_State.InitialState"
        self._conn.send("SetValue", self._path, f' "{base}.CartesianX" {x}')
        self._conn.send("SetValue", self._path, f' "{base}.CartesianY" {y}')
        self._conn.send("SetValue", self._path, f' "{base}.CartesianZ" {z}')
        self._conn.send("SetValue", self._path, f' "{base}.CartesianVX" {vx}')
        self._conn.send("SetValue", self._path, f' "{base}.CartesianVY" {vy}')
        self._conn.send("SetValue", self._path, f' "{base}.CartesianVZ" {vz}')
        if epoch:
            self._conn.send("SetValue", self._path, f' "{base}.Epoch" "{epoch}"')
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
        self._conn.send(
            "SetValue",
            self._path,
            f' "{self._path}/MassProperties.TotalMass" {total_mass}',
        )
        return self

    def set_stage_mass(
        self,
        dry_mass: float,
        wet_mass: float,
    ) -> "SatelliteBuilder":
        """
        Set the satellite's dry and wet (propellant) mass for stage modeling.

        Returns
        -------
        self
        """
        self._conn.send(
            "SetValue",
            self._path,
            f' "{self._path}/MassProperties.DryMass" {dry_mass}',
        )
        self._conn.send(
            "SetValue",
            self._path,
            f' "{self._path}/MassProperties.WetMass" {wet_mass}',
        )
        return self

    # ------------------------------------------------------------------
    # Attitude
    # ------------------------------------------------------------------

    def set_attitude(
        self,
        attitude_type: str,
        q1: float = 0,
        q2: float = 0,
        q3: float = 0,
        q4: float = 1,
    ) -> "SatelliteBuilder":
        """
        Set the satellite's attitude type and optional quaternion.

        Parameters
        ----------
        attitude_type : str
            One of ``"CBF"``, ``"J2000"``, ``"NV"``, ``"TLE"``.
        q1-q4 : float
            Quaternion components (qx, qy, qz, qs). Default is (0,0,0,1) = identity.

        Returns
        -------
        self
        """
        valid_types = {"CBF", "J2000", "NV", "TLE"}
        if attitude_type not in valid_types:
            raise _ex.ATKValueError(
                f"Unknown attitude type {attitude_type!r}. Valid: {valid_types}"
            )
        self._conn.send("SetAttitude", self._path, f' "{attitude_type}" {q1} {q2} {q3} {q4}')
        return self

    # ------------------------------------------------------------------
    # Graphics / visualisation
    # ------------------------------------------------------------------

    def set_color(self, color_index: int) -> "SatelliteBuilder":
        """
        Set the satellite's graphics color by ATK color index.

        Parameters
        ----------
        color_index : int
            ATK color table index (0 = default, 12 = red, etc.).

        Returns
        -------
        self
        """
        self._conn.send("Graphics", self._path, f" SetColor {color_index}")
        return self

    # ------------------------------------------------------------------
    # Run / propagate
    # ------------------------------------------------------------------

    def run_mcs(self) -> "SatelliteBuilder":
        """
        Run the Mission Control Sequence (MCS) for this satellite.

        Returns
        -------
        self
        """
        self._conn.send("RunMCS", self._path, "")
        return self

    # ------------------------------------------------------------------
    # String representation
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"<SatelliteBuilder name={self._name!r} path={self._path!r}>"
