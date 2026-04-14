"""
ATK Connect Mode — Coverage Analysis Helpers

Provides a fluent API for creating coverage definitions,
adding assets/facilities, and computing access statistics.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from atk import utils

if TYPE_CHECKING:
    from atk.connect.session import ATKConnection


class CoverageBuilder:
    """
    Fluent builder for ATK Coverage Definition objects.

    Created via ``atk.create_coverage('CoverageName')``.

    Example::

        cov = atk.create_coverage('GroundCoverage')
        cov.add_asset('*/Satellite/Sat1')
        cov.add_facility('*/Facility/Station1')
        cov.set_grid_resolution(lat_step=1.0, lon_step=1.0)
        stats = cov.compute_stats()
    """

    def __init__(self, conn: "ATKConnection", name: str):
        self._conn = conn
        self._name = utils.validate_name(name)
        self._path = f"*/CoverageDefinition/{self._name}"
        self._assets: list[str] = []
        self._facilities: list[str] = []

    @property
    def name(self) -> str:
        return self._name

    @property
    def path(self) -> str:
        return self._path

    def create(self) -> "CoverageBuilder":
        """Create the coverage definition object in ATK."""
        self._conn.send("New", self._path, "")
        return self

    def add_asset(self, sat_path: str) -> "CoverageBuilder":
        """
        Add a satellite as a coverage asset.

        Parameters
        ----------
        sat_path : str
            Satellite ATK path (e.g. ``"*/Satellite/Sat1"``).

        Returns
        -------
        self
        """
        sat_path = utils.resolve_path(sat_path)
        self._assets.append(sat_path)
        self._conn.send("Cov_AddAsset", self._path, f' "{sat_path}"')
        return self

    def add_facility(self, facility_path: str) -> "CoverageBuilder":
        """
        Add a ground facility as a coverage target.

        Parameters
        ----------
        facility_path : str
            Facility ATK path (e.g. ``"*/Facility/Station1"``).

        Returns
        -------
        self
        """
        facility_path = utils.resolve_path(facility_path)
        self._facilities.append(facility_path)
        self._conn.send("Cov_AddFacility", self._path, f' "{facility_path}"')
        return self

    def set_grid_resolution(
        self,
        lat_step: float = 1.0,
        lon_step: float = 1.0,
        grid_type: str = "LatLon",
    ) -> "CoverageBuilder":
        """
        Set the coverage grid resolution.

        Parameters
        ----------
        lat_step : float
            Latitude step in degrees.
        lon_step : float
            Longitude step in degrees.
        grid_type : str
            Grid type (e.g. ``"LatLon"``, ``"Custom"``).

        Returns
        -------
        self
        """
        self._conn.send(
            "Cov_SetGrid",
            self._path,
            f' "{grid_type}" {lat_step} {lon_step}',
        )
        return self

    def set_fom(
        self,
        fom_name: str,
        asset_path: str | None = None,
    ) -> "CoverageBuilder":
        """
        Attach a Figure of Merit (FOM) to the coverage definition.

        Parameters
        ----------
        fom_name : str
            FOM name (e.g. ``"SimpleAER"``, ``"Distance"``).
        asset_path : str, optional
            Asset path for the FOM.

        Returns
        -------
        self
        """
        if asset_path:
            self._conn.send(
                "Cov_SetFOM",
                self._path,
                f' "{fom_name}" "{utils.resolve_path(asset_path)}"',
            )
        else:
            self._conn.send("Cov_SetFOM", self._path, f' "{fom_name}"')
        return self

    def compute_stats(
        self,
        time_period: str = "*",
    ) -> CoverageStats:
        """
        Compute coverage statistics.

        Parameters
        ----------
        time_period : str
            Time period string (e.g. ``"*"`` for all time).

        Returns
        -------
        CoverageStats
            Object containing access count, total access time, etc.
        """
        raw = self._conn.send("Cov_Compute", self._path, f" {time_period}")
        return CoverageStats(raw)

    def __repr__(self) -> str:
        return f"<CoverageBuilder name={self._name!r}>"


class CoverageStats:
    """
    Parsed coverage computation result.

    Attributes
    ----------
    raw : CMDRESULT
        Raw ATK result object.
    access_count : int
        Number of access intervals.
    total_access_time : float
        Total access time in seconds.
    mean_access_duration : float
        Mean duration of each access interval.
    """

    def __init__(self, raw):
        self.raw = raw
        self._data = utils.result_to_list(raw)
        self._parsed = self._parse()

    def _parse(self) -> dict:
        """Parse the raw CMDRESULT data into a dict."""
        data = self._data
        if not data:
            return {}
        # Coverage stats are typically returned as key=value pairs
        result = {}
        for item in data:
            if "=" in item:
                key, val = item.split("=", 1)
                result[key.strip()] = val.strip()
            else:
                # Try positional: [count, total_time, mean_dur, ...]
                pass
        return result

    @property
    def access_count(self) -> int:
        return int(self._parsed.get("AccessCount", 0))

    @property
    def total_access_time(self) -> float:
        return float(self._parsed.get("TotalAccessTime", 0.0))

    @property
    def mean_access_duration(self) -> float:
        return float(self._parsed.get("MeanAccessDuration", 0.0))

    def __repr__(self) -> str:
        return (
            f"<CoverageStats access_count={self.access_count} "
            f"total_time={self.total_access_time:.2f}s>"
        )


# ---------------------------------------------------------------------------
# Add create_coverage() to ATKConnection
# ---------------------------------------------------------------------------

def _patch_connection():
    from atk.connect import session as _s

    def create_coverage(self, name: str) -> CoverageBuilder:
        """Create a new CoverageDefinition and return a CoverageBuilder."""
        builder = CoverageBuilder(self, name)
        builder.create()
        return builder

    _s.ATKConnection.create_coverage = create_coverage


_patch_connection()
del _patch_connection
