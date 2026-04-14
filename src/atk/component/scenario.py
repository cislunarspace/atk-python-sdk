"""
ATK Component Mode — Scenario Builder

Wraps ``IScenario`` with a Pythonic fluent API.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from atk.component.session import ComponentSession


class ScenarioBuilder:
    """
    Pythonic wrapper around ATK's ``IScenario`` (Component mode).

    Created via :meth:`ComponentSession.new_scenario()` or
    :meth:`ComponentSession.load_scenario()`.

    Example::

        with component_session() as session:
            scenario = session.new_scenario('MyMission')
            scenario.set_analysis_period('1 Jan 2024', '7 Jan 2024')
            sat = scenario.create_satellite('Sat1')
            ...
    """

    def __init__(self, session: "ComponentSession", scenario_obj: Any):
        self._session = session
        self._scenario = scenario_obj

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        """Return the scenario's instance name."""
        return self._scenario.GetInstanceName()

    @property
    def path(self) -> str:
        """Return the scenario's full ATK path."""
        return self._scenario.GetPath()

    @property
    def scenario(self) -> Any:
        """Return the raw ``IScenario`` SWIG object."""
        return self._scenario

    # ------------------------------------------------------------------
    # Time configuration
    # ------------------------------------------------------------------

    def set_analysis_period(self, start: str, stop: str) -> "ScenarioBuilder":
        """
        Set the analysis time period.

        Parameters
        ----------
        start : str
            Start time string (e.g. ``"5 Nov 2022 00:00:00.000"``).
        stop : str
            Stop time string.
        """
        self._scenario.SetTimePeriod(start, stop)
        return self

    def set_start_time(self, start: str) -> "ScenarioBuilder":
        """Set the scenario start time."""
        self._scenario.SetStartTime(start)
        return self

    def set_stop_time(self, stop: str) -> "ScenarioBuilder":
        """Set the scenario stop time."""
        self._scenario.SetStopTime(stop)
        return self

    def get_start_time(self) -> str:
        """Return the scenario start time as a string."""
        return self._scenario.GetStartTime()

    def get_stop_time(self) -> str:
        """Return the scenario stop time as a string."""
        return self._scenario.GetStopTime()

    # ------------------------------------------------------------------
    # Scenario lifecycle
    # ------------------------------------------------------------------

    def save(self, path: str | None = None) -> "ScenarioBuilder":
        """
        Save the scenario.

        Parameters
        ----------
        path : str, optional
            Save path. If omitted, saves to the scenario's current path.
        """
        if path:
            self._session.root.SaveScenario(path)
        else:
            self._session.root.SaveScenario()
        return self

    def close(self) -> None:
        """Close this scenario."""
        self._session.root.CloseScenario()

    # ------------------------------------------------------------------
    # Object creation
    # ------------------------------------------------------------------

    def create_satellite(self, name: str) -> Any:
        """
        Create a new satellite in this scenario.

        Parameters
        ----------
        name : str
            Satellite name.

        Returns
        -------
        ISatellite
            The raw SWIG satellite object.
            See :mod:`atk.component.satellite` for a higher-level wrapper.
        """
        children = self._scenario.GetChildren()
        sat = children.New(_get_enum("eSatellite"), name)
        return sat

    def get_object(self, path: str) -> Any:
        """
        Retrieve a child object by path (e.g. ``"Satellite/Sat1"``).

        Returns
        -------
        IAtkObject
        """
        return self._session.root.GetObjectFromPath(path)

    def get_satellites(self) -> list[Any]:
        """Return all satellites in this scenario."""
        children = self._scenario.GetChildren()
        return _collect_children_by_type(children, _get_enum("eSatellite"))

    # ------------------------------------------------------------------
    # Animation
    # ------------------------------------------------------------------

    def play(self) -> "ScenarioBuilder":
        """Start forward animation."""
        self._scenario.GetRoot().GetAnimation().PlayForward()
        return self

    def reset(self) -> "ScenarioBuilder":
        """Reset animation to the start time."""
        self._scenario.GetRoot().GetAnimation().Reset()
        return self

    # ------------------------------------------------------------------
    # String representation
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"<ScenarioBuilder name={self.name!r}>"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_enum(name: str) -> Any:
    """Resolve a propagator/object enum from the ATK module."""
    from atk.component import session as _s
    return getattr(_s._ATK, name)


def _collect_children_by_type(collection: Any, etype: Any) -> list[Any]:
    """Collect all children of a given type from an IAtkObjectCollection."""
    results = []
    for i in range(collection.GetCount()):
        item = collection.Item(i)
        if item.GetClassType() == etype:
            results.append(item)
    return results
