from dishka_faststream import inject, FromDishka
from faststream.rabbit import RabbitQueue, RabbitRouter, RabbitExchange, ExchangeType
from structlog import get_logger

from src.application.use_cases.validate_event_use_case import ValidateEventUseCase
from src.infrastructure.config import load_settings
from src.presentation.mappers import validation_mapper
from src.presentation.schemas import ValidationSchema

settings = load_settings()
log = get_logger("broker.consumer")


router = RabbitRouter()

exchange = RabbitExchange(
    name=settings.rabbit.consumer_exchange, type=ExchangeType.DIRECT, durable=True
)
validations_queue = RabbitQueue(
    name=settings.rabbit.consumer_queue,
    routing_key=settings.rabbit.consumer_queue,
    durable=True,
)


# @router.subscriber(validations_queue, exchange)
# @inject
# async def validations_handler(
#     body: ValidationSchema, use_case: FromDishka[ValidateEventUseCase]
# ):
#     log.info("Received validation event", body=body)
#     try:
#         result = await use_case.execute(validation_mapper.to_validation_request(body))
#     except Exception as exc:
#         log.exception("Failed to execute validation", exc=exc)
#         return {"error": str(exc)}
#     return validation_mapper.to_validation_response_schema(result)
