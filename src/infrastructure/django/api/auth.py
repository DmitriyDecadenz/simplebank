"""Async JWT bearer authentication for Django Ninja.

Decodes the bearer token via the framework-agnostic :class:`TokenService` (from
the DI container). On success the token subject (user id) becomes ``request.auth``
and the full payload is stashed on the request for downstream handlers.
"""

from __future__ import annotations

from ninja.security import HttpBearer

from domain.ports.token_service import TokenService
from infrastructure.django.di.container import container


class JWTAuth(HttpBearer):
    async def authenticate(self, request, token: str):
        token_service = await container.get(TokenService)
        try:
            payload = token_service.decode(token)
        except Exception:
            return None
        request.auth_payload = dict(payload)
        return payload.get("sub")
