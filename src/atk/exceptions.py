"""
ATK SDK custom exception hierarchy.
"""

from __future__ import annotations


class ATKError(Exception):
    """Base exception for all ATK SDK errors."""

    pass


class ATKConnectionError(ATKError):
    """Raised when connection to ATK fails (Connect mode)."""

    def __init__(self, host: str, port: int, message: str | None = None):
        self.host = host
        self.port = port
        detail = message or "Could not establish connection"
        super().__init__(f"[{host}:{port}] {detail}")


class ATKConnectionTimeout(ATKConnectionError):
    """Raised when connection to ATK times out."""

    def __init__(self, host: str, port: int, timeout: float):
        self.timeout = timeout
        super().__init__(host, port, f"Connection timed out after {timeout}s")


class ATKObjectNotFoundError(ATKError):
    """Raised when a path-based object lookup fails."""

    def __init__(self, path: str):
        self.path = path
        super().__init__(f"ATK object not found: {path}")


class ATKCommandError(ATKError):
    """Raised when an ATK Connect command returns an error."""

    def __init__(self, command: str, path: str, param: str, raw_response: str = ""):
        self.command = command
        self.path = path
        self.param = param
        self.raw_response = raw_response
        msg = f"Command '{command}' failed for '{path}'"
        if param:
            msg += f" with params: {param}"
        if raw_response:
            msg += f" — {raw_response}"
        super().__init__(msg)


class ATKScenarioError(ATKError):
    """Raised on scenario-level errors (load, save, create)."""

    pass


class ATKSatelliteError(ATKError):
    """Raised on satellite configuration/propagation errors."""

    pass


class ATKMCSError(ATKError):
    """Raised on MCS (Mission Control Sequence) build/run errors."""

    pass


class ATKReportError(ATKError):
    """Raised when report generation or parsing fails."""

    pass


class ATKComponentError(ATKError):
    """Raised on Component mode DLL loading or initialization errors."""

    pass


class ATKValueError(ATKError, ValueError):
    """Raised when an invalid value is provided (e.g. bad time string, bad orbital element)."""

    pass
