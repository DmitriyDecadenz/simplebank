"""JWT access-token service.

A minimal, dependency-free HS256 JSON Web Token implementation built on the
standard library. Tokens are standard-compliant (``header.payload.signature``
with base64url segments) and carry ``sub``, ``iat`` and ``exp`` claims.
"""

from __future__ import annotations

import base64
import hmac
import json
import time
from hashlib import sha256
from typing import Any, Mapping

from domain.ports.token_service import TokenService

_SUPPORTED_ALGORITHM = "HS256"


class TokenError(Exception):
    """Raised when a token is malformed, tampered with, or expired."""


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(segment: str) -> bytes:
    padding = "=" * (-len(segment) % 4)
    return base64.urlsafe_b64decode(segment + padding)


class JwtTokenService(TokenService):
    def __init__(
        self,
        secret_key: str,
        algorithm: str = _SUPPORTED_ALGORITHM,
        access_token_expire_minutes: int = 30,
    ) -> None:
        if algorithm != _SUPPORTED_ALGORITHM:
            raise ValueError(f"Unsupported JWT algorithm: {algorithm}")
        self._secret = secret_key.encode("utf-8")
        self._algorithm = algorithm
        self._expire_seconds = access_token_expire_minutes * 60

    def create_access_token(
        self, subject: str, claims: Mapping[str, Any] | None = None
    ) -> str:
        now = int(time.time())
        payload: dict[str, Any] = {
            "sub": subject,
            "iat": now,
            "exp": now + self._expire_seconds,
        }
        if claims:
            payload.update(claims)

        header = {"alg": self._algorithm, "typ": "JWT"}
        signing_input = f"{self._encode(header)}.{self._encode(payload)}"
        signature = self._sign(signing_input)
        return f"{signing_input}.{signature}"

    def decode(self, token: str) -> Mapping[str, Any]:
        try:
            header_b64, payload_b64, signature_b64 = token.split(".")
        except ValueError as exc:
            raise TokenError("Malformed token") from exc

        expected = self._sign(f"{header_b64}.{payload_b64}")
        if not hmac.compare_digest(expected, signature_b64):
            raise TokenError("Invalid token signature")

        try:
            payload = json.loads(_b64url_decode(payload_b64))
        except (ValueError, TypeError) as exc:
            raise TokenError("Malformed token payload") from exc

        if int(payload.get("exp", 0)) < int(time.time()):
            raise TokenError("Token has expired")
        return payload

    @staticmethod
    def _encode(data: Mapping[str, Any]) -> str:
        return _b64url_encode(json.dumps(data, separators=(",", ":")).encode("utf-8"))

    def _sign(self, signing_input: str) -> str:
        signature = hmac.new(
            self._secret, signing_input.encode("ascii"), sha256
        ).digest()
        return _b64url_encode(signature)
