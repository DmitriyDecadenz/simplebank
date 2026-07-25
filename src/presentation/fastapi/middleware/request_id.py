import uuid
from contextvars import ContextVar

from starlette.types import ASGIApp, Receive, Scope, Send

request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)


class RequestIdMiddleware:
    """
    Миддлварь для request_id
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "lifespan":
            await self.app(scope, receive, send)
            return

        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        request_id = headers.get(b"x-request-id", b"").decode() or str(uuid.uuid4())
        token = request_id_ctx.set(request_id)

        try:
            await self.app(scope, receive, send)
        finally:
            request_id_ctx.reset(token)
