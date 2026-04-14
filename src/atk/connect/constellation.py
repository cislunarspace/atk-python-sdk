"""
ATK Connect Mode — Constellation Builder and Batch Operations

Provides Walker constellation pattern generation and parallel
batch operations for multi-satellite analysis.
"""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import TYPE_CHECKING

from atk import exceptions as _ex
from atk import utils

if TYPE_CHECKING:
    from atk.connect.session import ATKConnection


class WalkerBuilder:
    """
    Build a Walker constellation using the Walker Delta pattern.

    Reference: Walker, J.G. (1971) "Satellite constellations".
    Pattern notation: ``T/P/F`` where T=total sats, P=planes, F=phase.

    Example::

        walker = atk.constellation_builder('Starlink')
        walker.walker_delta(
            num_satellites=60,
            num_planes=6,
            inc=53.0,
            alt=550.0,
        )
        walker.set_propagator('PropagatorSGP4')
        walker.run_all()
    """

    def __init__(
        self,
        conn: "ATKConnection",
        constellation_name: str,
        scenario_path: str = "*",
    ):
        self._conn = conn
        self._name = utils.validate_name(constellation_name)
        self._scenario_path = utils.resolve_path(scenario_path)
        self._path_prefix = f"{self._scenario_path}/Constellation/{self._name}"

        self._num_satellites = 0
        self._num_planes = 0
        self._inc = 0.0
        self._alt = 0.0
        self._phase_ratio = 0.0
        self._propagator = "PropagatorSGP4"
        self._sma: float | None = None
        self._sat_builders: list = []  # SatelliteBuilder instances
        self._created = False

    # ------------------------------------------------------------------
    # Walker Delta configuration
    # ------------------------------------------------------------------

    def walker_delta(
        self,
        num_satellites: int,
        num_planes: int,
        inc: float,
        alt: float,
    ) -> "WalkerBuilder":
        """
        Configure a Walker Delta constellation.

        Parameters
        ----------
        num_satellites : int
            Total number of satellites (T).
        num_planes : int
            Number of orbital planes (P). Must divide T evenly.
        inc : float
            Inclination in degrees.
        alt : float
            Altitude in km.

        Returns
        -------
        self
        """
        if num_satellites <= 0 or num_planes <= 0:
            raise _ex.ATKValueError(
                f"num_satellites and num_planes must be positive, "
                f"got {num_satellites}, {num_planes}"
            )
        if num_satellites % num_planes != 0:
            raise _ex.ATKValueError(
                f"num_satellites ({num_satellites}) must be divisible "
                f"by num_planes ({num_planes})"
            )

        self._num_satellites = num_satellites
        self._num_planes = num_planes
        self._inc = inc
        self._alt = alt

        # Phase ratio F = satellites_per_plane / (1 + satellites_per_plane)
        sats_per_plane = num_satellites // num_planes
        self._phase_ratio = sats_per_plane / (num_planes * (sats_per_plane - 1) + 1)

        # Approximate SMA from altitude (circular orbit, Earth radius ~6371 km)
        self._sma = alt + 6371.0

        return self

    def set_propagator(self, propagator: str) -> "WalkerBuilder":
        """
        Set the propagator type for all satellites in the constellation.

        Returns
        -------
        self
        """
        self._propagator = propagator
        return self

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def build(self) -> "WalkerBuilder":
        """
        Generate the constellation — create the constellation container
        and all satellite objects with their orbital elements.

        Returns
        -------
        self
        """
        if self._created:
            return self

        # Create constellation container
        self._conn.send("New", self._path_prefix, "")
        self._created = True

        sats_per_plane = self._num_satellites // self._num_planes
        sats_in_plane = 0

        for sat_idx in range(self._num_satellites):
            plane_idx = sat_idx // sats_per_plane
            intra_plane_idx = sat_idx % sats_per_plane

            # RAAN spacing: 360 / num_planes per plane
            raan = (360.0 / self._num_planes) * plane_idx

            # Phase offset: (360 / num_satellites) * phase_ratio * intra_plane_idx
            # applied per plane offset
            phase_offset = (360.0 / self._num_satellites) * self._phase_ratio * plane_idx
            ta = (360.0 / sats_per_plane) * intra_plane_idx + phase_offset

            sat_name = f"{self._name}_P{plane_idx}_S{intra_plane_idx}"
            sat_path = f"{self._path_prefix}/Satellite/{sat_name}"

            self._conn.send("New", sat_path, "")
            self._conn.send("SetPropagator", sat_path, f' "{self._propagator}"')

            # Set Keplerian elements
            base = f"{sat_path}/MainSequence.SegmentList.Initial_State.InitialState.Keplerian"
            self._conn.send("SetValue", sat_path, f' "{base}.sma" {self._sma}')
            self._conn.send("SetValue", sat_path, f' "{base}.ecc" 0.0')
            self._conn.send("SetValue", sat_path, f' "{base}.inc" {self._inc}')
            self._conn.send("SetValue", sat_path, f' "{base}.raan" {raan}')
            self._conn.send("SetValue", sat_path, f' "{base}.argp" 0.0')
            self._conn.send("SetValue", sat_path, f' "{base}.ta" {ta}')

            sats_in_plane += 1
            if sats_in_plane >= sats_per_plane:
                sats_in_plane = 0

        return self

    # ------------------------------------------------------------------
    # Batch MCS run
    # ------------------------------------------------------------------

    def run_all(self, max_workers: int = 8) -> dict[str, bool]:
        """
        Run MCS for all satellites in the constellation using a thread pool.

        Parameters
        ----------
        max_workers : int
            Maximum concurrent connections to ATK. Default 8.
            Be careful not to overwhelm the ATK server.

        Returns
        -------
        dict[str, bool]
            Mapping of satellite name → success (True) or failure (False).
        """
        if not self._created:
            raise _ex.ATKError(
                "Call build() before run_all()."
            )

        sats_per_plane = self._num_satellites // self._num_planes
        results: dict[str, bool] = {}
        lock = threading.Lock()

        def run_sat(sat_idx: int) -> tuple[str, bool]:
            plane_idx = sat_idx // sats_per_plane
            intra_plane_idx = sat_idx % sats_per_plane
            sat_name = f"{self._name}_P{plane_idx}_S{intra_plane_idx}"
            sat_path = f"{self._path_prefix}/Satellite/{sat_name}"
            try:
                self._conn.send("RunMCS", sat_path, "")
                return (sat_name, True)
            except Exception:
                return (sat_name, False)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(run_sat, i): i
                for i in range(self._num_satellites)
            }
            for future in as_completed(futures):
                name, success = future.result()
                with lock:
                    results[name] = success

        return results

    @property
    def satellite_count(self) -> int:
        return self._num_satellites

    def __repr__(self) -> str:
        return (
            f"<WalkerBuilder name={self._name!r} "
            f"sats={self._num_satellites} planes={self._num_planes} "
            f"inc={self._inc} alt={self._alt}>"
        )


# Fix typo: intra_builder_idx should be intra_plane_idx
# ---------------------------------------------------------------------------
# Add constellation_builder() to ATKConnection
# ---------------------------------------------------------------------------

def _patch_connection():
    from atk.connect import session as _s

    def constellation_builder(self, name: str) -> WalkerBuilder:
        """Create a Walker constellation builder."""
        return WalkerBuilder(self, name)

    _s.ATKConnection.constellation_builder = constellation_builder


_patch_connection()
del _patch_connection
