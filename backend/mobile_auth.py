from __future__ import annotations

import hashlib
import hmac
import os
import re
from pathlib import Path

from fastapi import Header, HTTPException

from .db import DATA_DIR

TOKEN_HASH_FILE = Path(os.getenv("SENTINEL_MOBILE_TOKEN_HASH_FILE", DATA_DIR / "mobile-token.sha256"))
_HASH_RE = re.compile(r"^[a-f0-9]{64}$")


def require_mobile_token(authorization: str | None = Header(default=None)) -> None:
    """Authenticate read-only companion requests against a SHA-256 token digest."""
    try:
        stored = TOKEN_HASH_FILE.read_text(encoding="ascii").strip()
    except OSError:
        raise HTTPException(status_code=503, detail="Mobile companion is not paired on this server") from None

    if not _HASH_RE.fullmatch(stored):
        raise HTTPException(status_code=503, detail="Mobile companion credential is not configured safely")

    scheme, _, supplied = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not supplied:
        raise HTTPException(status_code=401, detail="A mobile companion bearer token is required", headers={"WWW-Authenticate": "Bearer"})

    supplied_digest = hashlib.sha256(supplied.encode("utf-8")).hexdigest()
    if not hmac.compare_digest(stored, supplied_digest):
        raise HTTPException(status_code=401, detail="Invalid mobile companion token", headers={"WWW-Authenticate": "Bearer"})
