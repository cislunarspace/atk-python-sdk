"""
ATK Connect Mode SDK
====================
Connect to a running ATK instance over TCP and send Connect commands.

Usage::

    from atk.connect import connect

    with connect('127.0.0.1', 6655) as atk:
        atk.new('Scenario', 'MyScenario')
        atk.create_satellite('Sat1')
"""

from atk.connect.session import ATKConnection, ATKConnectionManager
from atk.connect.session import connect

# Import submodules to trigger their _patch_connection() calls, which add
# factory methods (create_scenario, create_satellite, constellation_builder,
# create_coverage, mcs_builder) to ATKConnection.
from atk.connect import scenario  # noqa: F401
from atk.connect import satellite  # noqa: F401
from atk.connect import mcs  # noqa: F401
from atk.connect import coverage  # noqa: F401
from atk.connect import constellation  # noqa: F401

__all__ = [
    "ATKConnection",
    "ATKConnectionManager",
    "connect",
]
