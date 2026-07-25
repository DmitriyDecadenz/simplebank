import asyncio
from contextlib import asynccontextmanager

from dishka.integrations.fastapi import setup_dishka
from dishka_faststream import setup_dishka as setup_faststream_dishka
from fastapi import FastAPI
from faststream.rabbit import RabbitBroker
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from structlog import get_logger

from src.infrastructure.config import load_settings
from src.infrastructure.dependencies.container import container
from src.infrastructure.logging import configure_logging
from src.presentation.broker.consumer import router as consumer_router

# from src.infrastructure.event_bus.faststream.broker import broker
from src.presentation.fastapi.router import router as validation_router

log = get_logger("main")
settings = load_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):

    configure_logging(json_logs=False)
    log.info("setup logging")
    broker: RabbitBroker = await container.get(RabbitBroker)
    broker.include_router(consumer_router)

    setup_faststream_dishka(container=container, broker=broker, auto_inject=True)

    try:
        await asyncio.wait_for(
            broker.start(),
            timeout=10.0,
        )
        log.info("start broker")
    except Exception as e:
        raise e

    yield

    await broker.stop()
    await container.close()
    log.info("broker stopped")
    yield


def create_application():
    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=settings.cors.allow_origins,
            allow_methods=settings.cors.allow_methods,
            allow_headers=settings.cors.allow_headers,
            allow_credentials=settings.cors.allow_credentials,
            expose_headers=settings.cors.expose_headers,
            max_age=settings.cors.max_age,
        ),
    ]
    _app = FastAPI(
        title="Smr Express Validator",
        description="",
        lifespan=lifespan,
        middleware=middleware,
        docs_url="/docs",
        root_path=settings.app.root_path,
    )

    setup_dishka(container, _app)

    _app.include_router(validation_router)

    return _app


app = create_application()

Instrumentator().instrument(app).expose(app)


@app.get("/health/ready")
async def status_ready():
    return {"status": "ok"}


@app.get("/health/live")
async def status_ready():
    return {"status": "ok"}
