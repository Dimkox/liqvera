"""Network-free read-only analyzer distribution."""

from liqvera_readonly_analyzer.frozen_package.reader import FrozenPackageEvidenceReader
from liqvera_readonly_analyzer.frozen_package.types import (
    FrozenPackageError,
    FrozenPackageErrorCode,
)

__all__ = [
    "FrozenPackageEvidenceReader",
    "FrozenPackageError",
    "FrozenPackageErrorCode",
    "__version__",
]

__version__ = "0.2.0"
