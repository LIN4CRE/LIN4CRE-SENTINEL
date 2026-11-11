from __future__ import annotations

import argparse
import hashlib
import os
import secrets

from .mobile_auth import TOKEN_HASH_FILE


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or rotate a read-only SENTINEL Android companion token.")
    parser.add_argument("--rotate", action="store_true", help="replace an existing companion token")
    args = parser.parse_args()

    if TOKEN_HASH_FILE.exists() and not args.rotate:
        parser.error(f"A token already exists at {TOKEN_HASH_FILE}; use --rotate to invalidate it and create a new one")

    TOKEN_HASH_FILE.parent.mkdir(parents=True, exist_ok=True)
    token = secrets.token_urlsafe(32)
    temporary = TOKEN_HASH_FILE.with_suffix(TOKEN_HASH_FILE.suffix + ".tmp")
    temporary.write_text(hashlib.sha256(token.encode("utf-8")).hexdigest() + "\n", encoding="ascii")
    try:
        os.chmod(temporary, 0o600)
    except OSError:
        pass  # Windows ACLs are managed by the user account; document file protection.
    temporary.replace(TOKEN_HASH_FILE)
    try:
        os.chmod(TOKEN_HASH_FILE, 0o600)
    except OSError:
        pass

    print("SENTINEL Android companion token (shown once; store it in the Android app):")
    print(token)
    print(f"Digest stored at: {TOKEN_HASH_FILE}")
    print("The companion API is read-only. Never share this token or send it over plain HTTP.")


if __name__ == "__main__":
    main()
