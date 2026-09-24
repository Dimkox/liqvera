"""Stable identities and error codes for frozen evidence packages.

Rewritten from PR #21 `_frozen_types.py` at
`7fe6918690f8bc1da5826c67e3619de4126e4f54`. Writer/publication codes are not
exported as package capabilities.
"""

from __future__ import annotations

from enum import StrEnum

PACKAGE_SCHEMA = "mee-readonly-frozen-package/v1"


class FrozenPackageErrorCode(StrEnum):
    INVALID_ARGUMENT = "INVALID_ARGUMENT"
    MANIFEST_MISSING = "MANIFEST_MISSING"
    MANIFEST_NON_CANONICAL = "MANIFEST_NON_CANONICAL"
    MANIFEST_HASH_INVALID = "MANIFEST_HASH_INVALID"
    MANIFEST_HASH_MISMATCH = "MANIFEST_HASH_MISMATCH"
    UNSUPPORTED_VERSION = "UNSUPPORTED_VERSION"
    MEMBER_SET_MISMATCH = "MEMBER_SET_MISMATCH"
    MEMBER_HASH_MISMATCH = "MEMBER_HASH_MISMATCH"
    MEMBER_HASH_INVALID = "MEMBER_HASH_INVALID"
    SYMLINK_FORBIDDEN = "SYMLINK_FORBIDDEN"
    PATH_INVALID = "PATH_INVALID"
    RECORD_INVALID = "RECORD_INVALID"
    RUN_MISMATCH = "RUN_MISMATCH"


class FrozenPackageError(ValueError):
    def __init__(self, code: FrozenPackageErrorCode) -> None:
        self.code = code
        super().__init__(code.value)
