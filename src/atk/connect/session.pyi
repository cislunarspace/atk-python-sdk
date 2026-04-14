"""Type stubs for ATKConnection — declares monkey-patched factory methods."""

from __future__ import annotations

from typing import Any, Generator

from atk.connect.constellation import WalkerBuilder
from atk.connect.coverage import CoverageBuilder
from atk.connect.mcs import McsBuilder
from atk.connect.satellite import SatelliteBuilder
from atk.connect.scenario import ScenarioBuilder

class ATKConnection:
    con_id: int
    host: str
    port: int
    is_connected: bool

    def __init__(self, con_id: int, host: str, port: int) -> None: ...
    def send(self, command: str, obj_path: str = "*", param: str = "") -> Any: ...
    def send_str(self, command: str, obj_path: str = "*", param: str = "") -> str: ...
    def close(self) -> None: ...

    # Factory methods injected by _patch_connection() at import time
    def create_scenario(self, name: str) -> ScenarioBuilder: ...
    def create_satellite(self, name: str, **kwargs: Any) -> SatelliteBuilder: ...
    def mcs_builder(self, sat_path: str) -> McsBuilder: ...
    def create_coverage(self, name: str) -> CoverageBuilder: ...
    def constellation_builder(self, name: str) -> WalkerBuilder: ...

class ATKConnectionManager:
    host: str
    port: int
    timeout: float
    retries: int
    backoff: float
    def __init__(
        self,
        host: str = ...,
        port: int = ...,
        timeout: float = ...,
        retries: int = ...,
        backoff: float = ...,
    ) -> None: ...
    def connect(self) -> ATKConnection: ...

def connect(
    host: str = ...,
    port: int = ...,
    timeout: float = ...,
    retries: int = ...,
    backoff: float = ...,
) -> Generator[ATKConnection, None, None]: ...
