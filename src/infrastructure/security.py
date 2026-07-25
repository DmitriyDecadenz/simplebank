"""Password hashing implementation.

Uses PBKDF2-HMAC-SHA256 from the standard library so no extra dependency is
required. The produced string is self-describing
(``pbkdf2_sha256$iterations$salt$hash``) so :meth:`verify` can re-derive the key
with the exact parameters used at hashing time.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets

from domain.ports.password_hasher import PasswordHasher

_ALGORITHM = "pbkdf2_sha256"
_ITERATIONS = 480_000
_SALT_BYTES = 16


def _b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")


def _unb64(value: str) -> bytes:
    return base64.b64decode(value.encode("ascii"))


class Pbkdf2PasswordHasher(PasswordHasher):
    def __init__(self, iterations: int = _ITERATIONS) -> None:
        self._iterations = iterations

    def hash(self, plain_password: str) -> str:
        salt = secrets.token_bytes(_SALT_BYTES)
        derived = hashlib.pbkdf2_hmac(
            "sha256", plain_password.encode("utf-8"), salt, self._iterations
        )
        return f"{_ALGORITHM}${self._iterations}${_b64(salt)}${_b64(derived)}"

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        try:
            algorithm, iterations, salt_b64, hash_b64 = hashed_password.split("$")
            if algorithm != _ALGORITHM:
                return False
            salt = _unb64(salt_b64)
            expected = _unb64(hash_b64)
            derived = hashlib.pbkdf2_hmac(
                "sha256", plain_password.encode("utf-8"), salt, int(iterations)
            )
        except (ValueError, TypeError):
            return False
        return hmac.compare_digest(derived, expected)
