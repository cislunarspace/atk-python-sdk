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

__all__ = [
    "ATKConnection",
    "ATKConnectionManager",
    "connect",
]
