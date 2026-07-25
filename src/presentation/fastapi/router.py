from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, HTTPException

from src.application.use_cases.validate_event_use_case import ValidateEventUseCase
from src.domain.models import ValidationRuleConfig
from src.presentation.mappers import validation_mapper
from src.presentation.schemas import (
    UpdateRuleSchema,
    ValidationResponseSchema,
    ValidationRuleSchema,
    ValidationSchema,
)

router = APIRouter(tags=["api_router"])


# @router.post("/validate", response_model=ValidationResponseSchema)
# @inject
# async def validate(
#     body: ValidationSchema,
#     use_case: FromDishka[ValidateEventUseCase],
# ) -> ValidationResponseSchema:
#     """Проверка заявки по разным операциям"""
#     response = await use_case.execute(validation_mapper.to_validation_request(body))
#     return validation_mapper.to_validation_response_schema(response)
#
#
# @router.get("/validation_rules", response_model=list[ValidationRuleSchema])
# @inject
# async def get_rules(
#     unit_of_work: FromDishka[AbstractUnitOfWork],
# ) -> list[ValidationRuleSchema]:
#     """Возвращает конфигурацию всех правил валидации."""
#     async with unit_of_work:
#         rules = await unit_of_work.validation_rule.get_all()
#     return [validation_mapper.to_validation_rule_schema(r) for r in rules]
