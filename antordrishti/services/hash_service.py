"""
Antordrishti — Hash Service
SHA-256 and MD5 hash calculation for file integrity verification.
"""

import hashlib
import os
from typing import Tuple, Optional


def calculate_hashes(file_path: str) -> Tuple[str, str]:
    """Calculate SHA-256 and MD5 hashes for a file.

    Returns:
        Tuple of (sha256_hex, md5_hex). Empty strings on error.
    """
    if not os.path.exists(file_path):
        return ("", "")

    sha256 = hashlib.sha256()
    md5 = hashlib.md5()

    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
                md5.update(chunk)
        return (sha256.hexdigest(), md5.hexdigest())
    except Exception:
        return ("", "")


def verify_hash(file_path: str, expected_hash: str,
                algorithm: str = "sha256") -> Optional[bool]:
    """Verify a file against an expected hash.

    Returns:
        True if match, False if mismatch, None on error.
    """
    if not os.path.exists(file_path):
        return None

    try:
        h = hashlib.new(algorithm)
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest().lower() == expected_hash.lower()
    except Exception:
        return None
