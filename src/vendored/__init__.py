"""
Vendored ATK-provided SWIG bindings.

This package re-exports the raw SWIG-generated Connect bindings
(ATKConnectModule) so that atk.connect.session can import them.

ATK-provided files in this directory:
    ATKConnectModule.py       — SWIG Python wrapper
    _ATKConnectModule.pyd     — Windows extension
    _ATKConnectModule.so      — Linux x64 extension
    _ATKConnectModule.cpython-38-aarch64-linux-gnu.so  — Linux ARM64 extension
"""

import os
import sys

# Ensure this directory is on sys.path so the raw module imports work
_vendored_dir = os.path.dirname(__file__)
if _vendored_dir not in sys.path:
    sys.path.insert(0, _vendored_dir)

from ATKConnectModule import (
    InitConnector,
    atkOpen,
    atkConnect,
    atkClose,
    atkConnectEx,
    atkExecuteScript,
    atkExecuteCommand,
    CMDRESULT,
)

__all__ = [
    "InitConnector",
    "atkOpen",
    "atkConnect",
    "atkClose",
    "atkConnectEx",
    "atkExecuteScript",
    "atkExecuteCommand",
    "CMDRESULT",
]
