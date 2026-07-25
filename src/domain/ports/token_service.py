from __future__ import annotations

from typing import Any, Mapping, Protocol, runtime_checkable


@runtime_checkable
class TokenService(Protocol):
    """Port for issuing and validating access tokens.

    The concrete signing scheme (JWT/HS256, lifetime, secret) is an
    infrastructure concern; the application depends only on this abstraction.
    """

    def create_access_token(
        self, subject: str, claims: Mapping[str, Any] | None = None
    ) -> str:
        """Issue a signed access token for ``subject`` with optional claims."""
        ...

    def decode(self, token: str) -> Mapping[str, Any]:
        """Return the token payload, raising if it is invalid or expired."""
        ...
