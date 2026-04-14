"""
ATK Python SDK
==============
High-level Python wrappers for Analytical Toolkit (ATK).

Two operating modes:

- ``atk.connect`` — Connect mode: TCP connection to a running ATK instance.
  Requires ATK software to be running.

- ``atk.component`` — Component mode: direct DLL load, no ATK window needed.
  Runs in ATK's embedded Python environment.

Example usage (Connect mode)::

    from atk.connect import connect

    with connect('127.0.0.1', 6655) as atk:
        atk.new('Scenario', 'MyScenario')
        sat = atk.create_satellite('Sat1')
        sat.set_keplerian(sma=7100, ecc=0.001, inc=30)
        atk.run()

Example usage (Component mode)::

    from atk.component import session

    with session() as root:
        scenario = root.new_scenario('MyScenario')
        sat = scenario.create_satellite('Sat1')
        sat.set_propagator_type('PropagatorAstromaster')
        ...
"""

from atk import exceptions
from atk import utils

__version__ = "0.1.0"

__all__ = [
    "exceptions",
    "utils",
]
