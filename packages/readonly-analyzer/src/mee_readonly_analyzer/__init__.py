"""Network-free read-only analyzer distribution."""

from mee_readonly_analyzer.frozen_package.reader import FrozenPackageEvidenceReader
from mee_readonly_analyzer.frozen_package.types import (
    FrozenPackageError,
    FrozenPackageErrorCode,
)

__all__ = [
    "FrozenPackageEvidenceReader",
    "FrozenPackageError",
    "FrozenPackageErrorCode",
    "__version__",
]

__version__ = "0.1.0"
