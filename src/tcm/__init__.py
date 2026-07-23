"""Public access to Transient Coalition Memory.

Frozen synthetic reference: `BatchedReserveCellular` (Wave XI).
Active real-data experimental model: `ActiveCoalitionCellular` (ACI).
Awareness organ (experimental): `AwareCoalitionCellular` + `Mnemosheath`.
"""

from .awareness import Mnemosheath
from .experimental import (
    ActiveCoalitionCellular,
    AwareCoalitionCellular,
    CleanEvidenceCellular,
    DiagnosticContrastCellular,
    SensoryGatedCellular,
    SilenceEscapeCellular,
    SkewCorrectedCellular,
    WaveXVIIITrustCellular,
)
from .reference import BatchedReserveCellular, FairProvGraph

# Canonical alias for the active experimental real-data cell.
ActiveExperimentalCellular = ActiveCoalitionCellular

__all__ = [
    "ActiveCoalitionCellular",
    "ActiveExperimentalCellular",
    "AwareCoalitionCellular",
    "BatchedReserveCellular",
    "CleanEvidenceCellular",
    "DiagnosticContrastCellular",
    "FairProvGraph",
    "Mnemosheath",
    "SensoryGatedCellular",
    "SilenceEscapeCellular",
    "SkewCorrectedCellular",
    "WaveXVIIITrustCellular",
]
