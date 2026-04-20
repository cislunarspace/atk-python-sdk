"""
Stub ATKComponentPythonModule for testing.

This is a minimal mock that allows the component module to be imported
without the actual ATK installation. It provides mock enums and the
IAtkObjectRoot class.
"""

from unittest.mock import MagicMock


class IAtkObjectRoot:
    """Mock IAtkObjectRoot for testing."""

    def __init__(self):
        self._scenario = None

    def NewScenario(self, name: str):
        pass

    def GetCurrentScenario(self):
        return self._scenario

    def SetCurrentScenario(self, scenario):
        self._scenario = scenario

    def LoadScenario(self, path: str):
        pass

    def CloseScenario(self):
        self._scenario = None

    def SaveScenario(self, path: str | None = None):
        pass

    def GetObjectFromPath(self, path: str):
        return None

    def ObjectExists(self, path: str) -> bool:
        return False

    def GetAnimation(self):
        return MagicMock()

    def OutputDataReport(self, obj, report_type: str, start: str, stop: str, output_path: str | None = None):
        return output_path or "default_report.txt"


# Propagator enumerations
ePropagatorTwoBody = "ePropagatorTwoBody"
ePropagatorJ2Perturbation = "ePropagatorJ2Perturbation"
ePropagatorHPOP = "ePropagatorHPOP"
ePropagatorSGP4 = "ePropagatorSGP4"
ePropagatorStkExternal = "ePropagatorStkExternal"
ePropagatorAstromaster = "ePropagatorAstromaster"
ePropagatorGreatArc = "ePropagatorGreatArc"
ePropagatorSimpleAscent = "ePropagatorSimpleAscent"
ePropagatorJ4Perturbation = "ePropagatorJ4Perturbation"
ePropagatorVinti = "ePropagatorVinti"
ePropagatorBallistic = "ePropagatorBallistic"
ePropagatorLOP = "ePropagatorLOP"

# Object type enumerations
eSatellite = "eSatellite"
eScenario = "eScenario"
eFacility = "eFacility"
eCoverage = "eCoverage"
