"""
ATK Component Mode SDK
======================
Direct DLL access without requiring ATK software to be running.
Uses ATK's embedded Python environment via ATKComponentPythonModule.

Usage (within ATK's embedded Python interpreter)::

    from atk.component import session

    with session() as root:
        scenario = root.new_scenario('MyScenario')
        sat = scenario.create_satellite('Sat1')
        sat.set_propagator_type('PropagatorAstromaster')
        ...

Note: Component mode requires the ATKComponentPythonModule.pyd and
_ATKComponentPythonModule.pyd DLLs. These must be in the same directory
as ATKComponentPythonModule.py (typically the ATK installation root).
Copy both files to your project or add the ATK installation to your path.
"""

from atk.component.session import ComponentSession, component_session

__all__ = [
    "ComponentSession",
    "component_session",
]
