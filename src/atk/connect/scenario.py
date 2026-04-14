"""
ATK Connect Mode — Scenario Builder

Provides a fluent Python API for creating and configuring ATK scenarios
via Connect commands.
"""

from __future__ import annotations

from atk import exceptions as _ex
from atk import utils

from atk.connect.satellite import SatelliteBuilder
from atk.connect.session import ATKConnection


class ScenarioBuilder:
    """
    Fluent builder for ATK scenarios in Connect mode.

    Created via :meth:`ATKConnection.create_scenario() <atk.connect.session.ATKConnection.create_scenario>`
    or by calling ``ScenarioBuilder(atk_conn, "ScenarioName")`` directly.

    Example::

        scenario = atk.create_scenario('MyMission')
        scenario.set_analysis_period('1 Jan 2024 00:00:00', '7 Jan 2024 00:00:00')
        scenario.set_analysis_mode('Keplerian')
        scenario.save()
    """

    def __init__(self, conn: "ATKConnection", name: str):
        self._conn = conn
        self._name = utils.validate_name(name)
        # ATK Connect path for the scenario
        self._path = f"*/Scenario/{self._name}"

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        return self._name

    @property
    def path(self) -> str:
        return self._path

    # ------------------------------------------------------------------
    # Scenario lifecycle
    # ------------------------------------------------------------------

    def create(self) -> "ScenarioBuilder":
        """
        Set up (or create) the scenario in ATK.

        ATK always has a default scenario loaded when it starts.
        ``New / Scenario {name}`` creates a NEW scenario, which fails if
        a scenario is already loaded. This method handles that gracefully:
        if a scenario already exists (NACK from New), we simply use it —
        ``set_analysis_period()`` and other operations work regardless
        of which scenario is active.

        Returns
        -------
        self
        """
        # ATK New command format: obj='*', param=' Scenario {name}'
        # NACK is expected if a scenario is already loaded — that's fine.
        try:
            self._conn.send("New", "*", f" Scenario {self._name}")
        except Exception:
            # Scenario already exists; use it as-is
            pass
        return self

    def save(self, path: str | None = None) -> "ScenarioBuilder":
        """
        Save the scenario to a file.

        Parameters
        ----------
        path : str, optional
            Save path. If None, uses the scenario's current path.

        Returns
        -------
        self
        """
        if path:
            self._conn.send("Save", self._path, f' "{path}"')
        else:
            self._conn.send("Save", self._path, "")
        return self

    def load(self, path: str) -> "ScenarioBuilder":
        """
        Load a scenario from an XML file.

        Parameters
        ----------
        path : str
            Path to the scenario XML file.

        Returns
        -------
        self
        """
        self._conn.send("Load", "*", f' "{path}"')
        return self

    def unload(self) -> "ScenarioBuilder":
        """Unload the scenario from ATK memory."""
        self._conn.send("Unload", self._path, "")
        return self

    # ------------------------------------------------------------------
    # Time configuration
    # ------------------------------------------------------------------

    def set_analysis_period(
        self,
        start: str,
        stop: str,
    ) -> "ScenarioBuilder":
        """
        Set the analysis time period for the scenario.

        Parameters
        ----------
        start : str
            Start time in ATK format (e.g. ``"5 Nov 2022 00:00:00.000"``).
        stop : str
            Stop time in ATK format.

        Returns
        -------
        self
        """
        # Normalise path: use '*' for global (no specific scenario)
        self._conn.send(
            "SetAnalysisTimePeriod",
            "*",
            f' "{start}" "{stop}"',
        )
        return self

    def set_analysis_mode(
        self,
        mode: str = "Keplerian",
    ) -> "ScenarioBuilder":
        """
        Set the scenario's analysis mode.

        Parameters
        ----------
        mode : str
            One of ``"Keplerian"``, ``"Spice"``, ``"Fixed"``.

        Returns
        -------
        self
        """
        valid = {"Keplerian", "Spice", "Fixed"}
        if mode not in valid:
            raise _ex.ATKValueError(f"Invalid analysis mode {mode!r}. Must be one of {valid}.")
        self._conn.send("SetAnalysisMode", self._path, f' "{mode}"')
        return self

    # ------------------------------------------------------------------
    # Animation control
    # ------------------------------------------------------------------

    def animate(self, forward: bool = True) -> "ScenarioBuilder":
        """
        Start scenario animation.

        Parameters
        ----------
        forward : bool
            True for forward play (default), False for reverse.

        Returns
        -------
        self
        """
        direction = "Forward" if forward else "Reverse"
        self._conn.send("Animate", self._path, f' "{direction}"')
        return self

    def stop_animation(self) -> "ScenarioBuilder":
        """Stop scenario animation."""
        self._conn.send("Animate", self._path, ' "Stop"')
        return self

    # ------------------------------------------------------------------
    # 2D/3D windows
    # ------------------------------------------------------------------

    def open_2d_window(self, name: str = "2D") -> "ScenarioBuilder":
        """Open a 2D graphics window for this scenario."""
        self._conn.send("Window2D", self._path, f' "{name}"')
        return self

    def open_3d_window(self, name: str = "3D") -> "ScenarioBuilder":
        """Open a 3D graphics window for this scenario."""
        self._conn.send("Window3D", self._path, f' "{name}"')
        return self

    # ------------------------------------------------------------------
    # Report shortcuts
    # ------------------------------------------------------------------

    def quick_report(
        self,
        obj_path: str,
        style: str,
        time_period: str | None = None,
    ) -> "ATKConnection":
        """
        Generate a quick report for an object.

        Parameters
        ----------
        obj_path : str
            Object path within the scenario.
        style : str
            Report style name.
        time_period : str, optional
            Time period string (e.g. ``"*"`` for all time).

        Returns
        -------
        CMDRESULT
            The raw ATK report result. See :mod:`atk.connect.reports` for
            a higher-level wrapper.
        """
        if time_period:
            return self._conn.send(
                "QuickReport_" + style.replace(" ", ""),
                obj_path,
                f' {time_period}',
            )
        return self._conn.send(
            "QuickReport_" + style.replace(" ", ""),
            obj_path,
            "",
        )

    # ------------------------------------------------------------------
    # String representation
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"<ScenarioBuilder name={self._name!r} path={self._path!r}>"


# ---------------------------------------------------------------------------
# ATKConnection extension — add builder factories
# ---------------------------------------------------------------------------

def _scenario_builder_factory(conn: "ATKConnection", name: str) -> ScenarioBuilder:
    """Create and register a ScenarioBuilder for the connection."""
    builder = ScenarioBuilder(conn, name)
    builder.create()
    return builder


def _satellite_builder_factory(conn: "ATKConnection", name: str, **kwargs) -> "SatelliteBuilder":
    """Create and register a SatelliteBuilder for the connection."""
    builder = SatelliteBuilder(conn, name, **kwargs)
    builder.create()
    return builder


# Monkey-patch ATKConnection with builder methods (applied after import)
def _patch_connection():
    from atk.connect import session as _s

    def create_scenario(self, name: str) -> ScenarioBuilder:
        """Create a new scenario and return a ScenarioBuilder."""
        return _scenario_builder_factory(self, name)

    def create_satellite(self, name: str, **kwargs) -> "SatelliteBuilder":
        """Create a new satellite and return a SatelliteBuilder."""
        return _satellite_builder_factory(self, name, **kwargs)

    _s.ATKConnection.create_scenario = create_scenario
    _s.ATKConnection.create_satellite = create_satellite


_patch_connection()
del _patch_connection
