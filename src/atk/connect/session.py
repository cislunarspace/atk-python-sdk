"""
ATK Connect Mode — Session Management

Provides ``ATKConnection`` (raw connection) and ``connect()`` (context manager).
"""

from __future__ import annotations

import time
import warnings
from contextlib import contextmanager
from typing import Any, Generator

from atk import exceptions as _ex
from atk import utils

# ---------------------------------------------------------------------------
# Raw SWIG imports — from vendored/ (sibling of atk/ under src/)
# ---------------------------------------------------------------------------
import os
import sys

# vendored/ lives at src/vendored/ (sibling of atk/). Resolve it relative
# to this file: src/atk/connect/session.py → up 3 levels → src/ → vendored/
_vendored_dir = os.path.join(os.path.dirname(__file__), "..", "..", "vendored")
_vendored_dir = os.path.normpath(_vendored_dir)
if _vendored_dir not in sys.path:
    sys.path.insert(0, _vendored_dir)

try:
    import ATKConnectModule as _ATK
except ImportError as _exc:  # pragma: no cover
    raise ImportError(
        "ATKConnectModule not found in src/vendored/. "
        "Ensure the SDK is installed with: pip install -e ."
    ) from _exc


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 6655
CONNECT_TIMEOUT = 30.0  # seconds
RETRY_ATTEMPTS = 3
RETRY_BACKOFF = 2.0  # seconds


# ---------------------------------------------------------------------------
# ATKConnection — connection handle wrapper
# ---------------------------------------------------------------------------

class ATKConnection:
    """
    Thin wrapper around an ATK Connect-mode TCP connection.

    Attributes
    ----------
    con_id : int
        The connection handle returned by ``atkOpen``.
    host : str
        Remote host address.
    port : int
        TCP port number.
    is_connected : bool
        True while the connection is open.
    """

    __slots__ = ("con_id", "host", "port", "_connected")

    def __init__(self, con_id: int, host: str, port: int):
        self.con_id = con_id
        self.host = host
        self.port = port
        self._connected = True

    @property
    def is_connected(self) -> bool:
        return self._connected

    # ------------------------------------------------------------------
    # Core ATK operations
    # ------------------------------------------------------------------

    def send(
        self,
        command: str,
        obj_path: str = "*",
        param: str = "",
    ) -> _ATK.CMDRESULT:
        """
        Send a Connect command to ATK and return the raw result.

        Parameters
        ----------
        command : str
            Connect command name (e.g. ``"New"``, ``"SetValue"``).
        obj_path : str
            Object path (e.g. ``"*/Satellite/Sat1"``). Use ``"*"`` or ``""`` for
            commands that don't target a specific object.
        param : str
            Parameter string for the command.

        Returns
        -------
        CMDRESULT
            SWIG wrapper containing ``m_vectData`` (list of strings) and ``Item()``.

        Raises
        ------
        ATKConnectionError
            If the connection has been closed.
        ATKCommandError
            If ATK returns an error string.
        """
        if not self._connected:
            raise _ex.ATKConnectionError(
                self.host, self.port,
                "Connection is closed"
            )

        # Normalise path
        obj_path = utils.resolve_path(obj_path)

        result = _ATK.atkConnect(self.con_id, command, obj_path, param)

        # CMDRESULT may carry an error string in m_vectData
        data = utils.result_to_list(result)
        if data and data[0].upper().rstrip(":").lstrip("-") in ("ERROR", "FAIL", "FALSE"):
            raise _ex.ATKCommandError(
                command, obj_path, param,
                raw_response=" ".join(data)
            )

        return result

    def send_str(
        self,
        command: str,
        obj_path: str = "*",
        param: str = "",
    ) -> str:
        """
        Like ``send()`` but return the response as a plain string.

        This is a convenience for commands that return a single string
        value (e.g. object names, status messages).
        """
        result = self.send(command, obj_path, param)
        data = utils.result_to_list(result)
        return " ".join(data)

    def close(self) -> None:
        """Close the TCP connection to ATK."""
        if self._connected:
            try:
                _ATK.atkClose(self.con_id)
            finally:
                self._connected = False

    def __repr__(self) -> str:
        status = "open" if self._connected else "closed"
        return f"<ATKConnection {self.host}:{self.port} [{status}]>"


# ---------------------------------------------------------------------------
# Connection manager with retry
# ---------------------------------------------------------------------------

class ATKConnectionManager:
    """
    Manage ATK connection lifecycle with automatic retry on failure.

    Parameters
    ----------
    host : str
        ATK server host. Defaults to ``"127.0.0.1"``.
    port : int
        ATK server port. Defaults to ``6655``.
    timeout : float
        Connection timeout in seconds. Defaults to ``30``.
    retries : int
        Number of retry attempts on connection failure. Defaults to ``3``.
    backoff : float
        Seconds to wait between retries. Defaults to ``2.0``.

    Example::

        mgr = ATKConnectionManager('127.0.0.1', 6655, retries=5)
        conn = mgr.connect()
        ...
        conn.close()
    """

    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        timeout: float = CONNECT_TIMEOUT,
        retries: int = RETRY_ATTEMPTS,
        backoff: float = RETRY_BACKOFF,
    ):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.retries = retries
        self.backoff = backoff

    def connect(self) -> ATKConnection:
        """
        Open a connection to the ATK server.

        Raises
        ------
        ATKConnectionError
            After all retry attempts are exhausted.
        """
        last_ex: Exception | None = None

        for attempt in range(1, self.retries + 1):
            try:
                con_id = _ATK.atkOpen(self.host, self.port)
                if con_id is not None and con_id != 0:
                    return ATKConnection(con_id, self.host, self.port)
            except Exception as err:  # pragma: no cover
                last_ex = err

            if attempt < self.retries:
                warnings.warn(
                    f"[{self.host}:{self.port}] Connection attempt {attempt} failed "
                    f"({type(last_ex).__name__}): {last_ex}. "
                    f"Retrying in {self.backoff}s... ({attempt}/{self.retries})",
                    RuntimeWarning,
                )
                time.sleep(self.backoff)

        raise _ex.ATKConnectionError(
            self.host, self.port,
            f"Failed after {self.retries} attempts: {last_ex}"
        )


# ---------------------------------------------------------------------------
# Context-manager factory
# ---------------------------------------------------------------------------

@contextmanager
def connect(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    timeout: float = CONNECT_TIMEOUT,
    retries: int = RETRY_ATTEMPTS,
    backoff: float = RETRY_BACKOFF,
) -> Generator[ATKConnection, None, None]:
    """
    Context-manager factory for ATK Connect mode.

    Usage::

        with connect() as atk:
            atk.send('New', '', '/ Scenario MyScenario')

        # or, with custom host/port:
        with connect('192.168.1.10', 6655) as atk:
            ...

    Yields
    ------
    ATKConnection
    """
    mgr = ATKConnectionManager(host, port, timeout, retries, backoff)
    conn = mgr.connect()
    try:
        yield conn
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Submodule lazy-import helpers — added in later phases
# ---------------------------------------------------------------------------

