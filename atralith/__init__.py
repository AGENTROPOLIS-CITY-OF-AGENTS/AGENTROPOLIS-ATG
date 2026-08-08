"""ATRALITH-lite — prototype ATG mandate, envelope, and receipt helpers.

This lightweight package builds mandate, envelope, and receipt artifacts and
checks their schema and hash consistency against supplied evidence. It does not
authenticate signers or create cryptographic authorization.
"""

__version__ = "0.1.0"

from atralith.mandate_builder import build, hash_mandate, validate

__all__ = ["build", "hash_mandate", "validate", "__version__"]
