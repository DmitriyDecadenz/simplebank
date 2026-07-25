from datetime import date

import httpx
import structlog

from src.domain.models import ActiveContract
from src.domain.ports.contracts_gateway import ContractsGateway
from src.infrastructure.config import load_settings

settings = load_settings()
logger = structlog.get_logger()


def _parse_contract(data: dict) -> ActiveContract:
    return ActiveContract(
        contract_id=data["contractId"],
        address=data["address"],
        insurer_inn=data["insurerInn"],
        territory=data["territory"],
        start_date=date.fromisoformat(data["startDate"]),
        end_date=date.fromisoformat(data["endDate"]),
    )


class HttpContractsGateway(ContractsGateway):
    """HTTP-реализация интеграции с smr-express-contracts."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client
        self._base_url = settings.contracts.url

    async def find_active_contracts(self, address: str) -> list[ActiveContract]:
        try:
            response = await self._client.get(
                f"{self._base_url}/api/v1/contracts/active",
                params={"address": address},
            )
            response.raise_for_status()
            return [_parse_contract(item) for item in response.json()]
        except httpx.HTTPError as exc:
            logger.warning("contracts_gateway_error", error=str(exc))
            return []

    async def find_active_contracts_by_contractor(
        self, inn: str, territory: str
    ) -> list[ActiveContract]:
        try:
            response = await self._client.get(
                f"{self._base_url}/api/v1/contracts/by-contractor",
                params={"inn": inn, "territory": territory},
            )
            response.raise_for_status()
            return [_parse_contract(item) for item in response.json()]
        except httpx.HTTPError as exc:
            logger.warning("contracts_gateway_error", error=str(exc))
            return []
