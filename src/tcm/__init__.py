"""Public access to Transient Coalition Memory.

Frozen synthetic reference: `BatchedReserveCellular` (Wave XI).
Active real-data experimental model: `ActiveCoalitionCellular` (ACI).
"""

from .experimental import (
    ActiveCoalitionCellular,
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
    "BatchedReserveCellular",
    "CleanEvidenceCellular",
    "DiagnosticContrastCellular",
    "FairProvGraph",
    "SensoryGatedCellular",
    "SilenceEscapeCellular",
    "SkewCorrectedCellular",
    "WaveXVIIITrustCellular",
]
