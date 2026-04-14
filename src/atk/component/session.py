"""
ATK Component Mode — Session Management

Provides ``ComponentSession`` (IAtkObjectRoot wrapper) and
``component_session()`` context manager.
"""

from __future__ import annotations

import os
import sys
from typing import Any

from atk import exceptions as _ex

# ---------------------------------------------------------------------------
# Locate ATK Component Python Module
# ---------------------------------------------------------------------------

# The ATK Component DLL + Python wrapper live in the ATK installation.
# By default we look next to this file's sibling _ATKComponentPythonModule.pyd,
# or in the ATK install dir.  Users may also set ATK_ROOT env var.

_ATK_ROOT_ENV = os.environ.get("ATK_ROOT", r"C:\Users\ouyan\ATK\ATK-v4.0-rc.4")

def _find_component_module() -> Any:
    """
    Locate and import ATKComponentPythonModule.

    Strategy:
    1. If already importable, use it.
    2. Try sibling directory of this file (project-local copy).
    3. Try ATK_ROOT from environment.
    4. Add to sys.path and retry.
    """
    try:
        import ATKComponentPythonModule as m
        return m
    except ImportError:
        pass

    candidates = [
        os.path.join(os.path.dirname(__file__), "..", "..", "vendored"),  # vendored/ at repo root
        os.path.join(os.path.dirname(__file__), "..", ".."),             # repo root
        os.path.join(_ATK_ROOT_ENV),                                     # ATK install
    ]

    for candidate in candidates:
        module_init = os.path.join(candidate, "ATKComponentPythonModule.py")
        if os.path.exists(module_init):
            if candidate not in sys.path:
                sys.path.insert(0, candidate)
            try:
                import ATKComponentPythonModule as m
                return m
            except ImportError:
                pass

    raise _ex.ATKComponentError(
        "ATKComponentPythonModule not found. "
        "Copy ATKComponentPythonModule.py and _ATKComponentPythonModule.pyd "
        "to this project directory, or set ATK_ROOT environment variable."
    )


# ---------------------------------------------------------------------------
# Import the module (may raise ATKComponentError above)
# ---------------------------------------------------------------------------
try:
    _ATK = _find_component_module()
except _ex.ATKComponentError:
    # Surface the error at import time with a clear message
    raise


# ---------------------------------------------------------------------------
# Propagator type enum values (from SWIG wrapper)
# ---------------------------------------------------------------------------
_PROPAGATOR_NAMES = {
    "PropagatorTwoBody":        getattr(_ATK, "ePropagatorTwoBody", None),
    "PropagatorJ2Perturbation": getattr(_ATK, "ePropagatorJ2Perturbation", None),
    "PropagatorHPOP":          getattr(_ATK, "ePropagatorHPOP", None),
    "PropagatorSGP4":          getattr(_ATK, "ePropagatorSGP4", None),
    "PropagatorStkExternal":   getattr(_ATK, "ePropagatorStkExternal", None),
    "PropagatorAstromaster":   getattr(_ATK, "ePropagatorAstromaster", None),
    "PropagatorGreatArc":      getattr(_ATK, "ePropagatorGreatArc", None),
    "PropagatorSimpleAscent":   getattr(_ATK, "ePropagatorSimpleAscent", None),
    "PropagatorJ4Perturbation": getattr(_ATK, "ePropagatorJ4Perturbation", None),
    "PropagatorVinti":         getattr(_ATK, "ePropagatorVinti", None),
    "PropagatorBallistic":     getattr(_ATK, "ePropagatorBallistic", None),
}


def _resolve_propagator_type(name_or_enum: Any) -> Any:
    """Convert a propagator name string to the SWIG enum value."""
    if isinstance(name_or_enum, str):
        enum = _PROPAGATOR_NAMES.get(name_or_enum)
        if enum is None:
            raise _ex.ATKValueError(
                f"Unknown propagator type {name_or_enum!r}. "
                f"Valid names: {list(k for k in _PROPAGATOR_NAMES if _PROPAGATOR_NAMES[k])}"
            )
        return enum
    return name_or_enum


# ---------------------------------------------------------------------------
# ComponentSession — IAtkObjectRoot wrapper
# ---------------------------------------------------------------------------

class ComponentSession:
    """
    High-level wrapper around ATK's ``IAtkObjectRoot`` for Component mode.

    Attributes
    ----------
    root : IAtkObjectRoot
        The underlying SWIG wrapper object.
    scenario : IScenario or None
        The currently loaded scenario (set by :meth:`load_scenario` or
        :meth:`new_scenario`).

    Example::

        with component_session() as session:
            session.new_scenario('MyScenario')
            sat = session.create_satellite('Sat1')
            ...
    """

    __slots__ = ("root", "_scenario")

    def __init__(self, root: Any):
        self.root = root
        self._scenario: Any = None

    # ------------------------------------------------------------------
    # Scenario lifecycle
    # ------------------------------------------------------------------

    def new_scenario(self, name: str) -> Any:
        """
        Create a new scenario.

        Parameters
        ----------
        name : str
            Scenario name.

        Returns
        -------
        IScenario
            The newly created scenario object.

        Raises
        ------
        ATKScenarioError
            If a scenario already exists.
        """
        if self._scenario is not None:
            raise _ex.ATKScenarioError(
                "A scenario is already loaded. Close it first with close_scenario()."
            )
        self.root.NewScenario(name)
        self._scenario = self.root.GetCurrentScenario()
        return self._scenario

    def load_scenario(self, path: str) -> Any:
        """
        Load an existing scenario from an XML file.

        Parameters
        ----------
        path : str
            Absolute or ATK-relative scenario path
            (e.g. ``"C:/ATK/Scenarios/Scenario1.xml"``).

        Returns
        -------
        IScenario
        """
        if self._scenario is not None:
            raise _ex.ATKScenarioError(
                "A scenario is already loaded. Close it first."
            )
        self.root.LoadScenario(path)
        self._scenario = self.root.GetCurrentScenario()
        return self._scenario

    def close_scenario(self) -> None:
        """Close the current scenario without saving."""
        if self._scenario is not None:
            self.root.CloseScenario()
            self._scenario = None

    def save_scenario(self, path: str | None = None) -> None:
        """
        Save the current scenario.

        Parameters
        ----------
        path : str, optional
            Save path. If omitted, saves to the scenario's current path
            (or prompts ATK to ask for one if it's a new scenario).
        """
        if self._scenario is None:
            raise _ex.ATKScenarioError("No scenario is currently loaded.")
        if path:
            self.root.SaveScenario(path)
        else:
            self.root.SaveScenario()

    @property
    def scenario(self) -> Any:
        """Return the currently loaded scenario (or None)."""
        return self._scenario

    @property
    def is_open(self) -> bool:
        return self._scenario is not None

    # ------------------------------------------------------------------
    # Object creation helpers
    # ------------------------------------------------------------------

    def create_satellite(self, name: str) -> Any:
        """
        Create a new satellite in the current scenario.

        Requires a scenario to be loaded first.

        Returns
        -------
        ISatellite wrapper (see ``atk.component.satellite`` for a higher-level class).
        """
        if self._scenario is None:
            raise _ex.ATKScenarioError("Create a scenario first with new_scenario() or load_scenario().")
        children = self._scenario.GetChildren()
        sat = children.New(_ATK.eSatellite, name)
        return sat

    def get_object(self, path: str) -> Any:
        """
        Retrieve an object by its ATK path (e.g. ``"Satellite/Sat1"``).

        Returns
        -------
        IAtkObject (cast to the appropriate type by the caller).
        """
        obj = self.root.GetObjectFromPath(path)
        if obj is None:
            raise _ex.ATKObjectNotFoundError(path)
        return obj

    def object_exists(self, path: str) -> bool:
        """Check whether an object exists at the given path."""
        return self.root.ObjectExists(path)

    # ------------------------------------------------------------------
    # Animation control
    # ------------------------------------------------------------------

    def play(self) -> None:
        """Start forward animation of the current scenario."""
        self.root.GetAnimation().PlayForward()

    def reset(self) -> None:
        """Reset animation to the start time."""
        self.root.GetAnimation().Reset()

    # ------------------------------------------------------------------
    # Report export
    # ------------------------------------------------------------------

    def output_report(
        self,
        obj: Any,
        report_type: str,
        start: str,
        stop: str,
        output_path: str | None = None,
    ) -> str:
        """
        Generate a data report and optionally save to a file.

        Parameters
        ----------
        obj : IAtkObject
            The object to generate the report for (e.g. ISatellite).
        report_type : str
            Report style name (e.g. ``"J2000 Position Velocity"``).
        start : str
            Start time string (ATK format, e.g. ``"5 Nov 2022 00:00:00.000"``).
        stop : str
            Stop time string.
        output_path : str, optional
            Output file path. If None, returns the default output path.

        Returns
        -------
        str
            Path to the generated report file.
        """
        if output_path:
            # ATK's OutputDataReport returns a path string
            return self.root.OutputDataReport(obj, report_type, start, stop, output_path)
        return self.root.OutputDataReport(obj, report_type, start, stop)

    def __repr__(self) -> str:
        scen = self._scenario.GetInstanceName() if self._scenario else "no scenario"
        return f"<ComponentSession scenario={scen!r}>"


# ---------------------------------------------------------------------------
# Context manager factory
# ---------------------------------------------------------------------------

def component_session() -> ComponentSession:
    """
    Context manager that creates and tears down an ATK Component session.

    Usage::

        with component_session() as session:
            session.new_scenario('MyScenario')
            ...

    Yields
    ------
    ComponentSession
    """
    root = _ATK.IAtkObjectRoot()
    session = ComponentSession(root)
    try:
        yield session
    finally:
        if session._scenario is not None:
            session.root.CloseScenario()


__all__ = [
    "ComponentSession",
    "component_session",
]
