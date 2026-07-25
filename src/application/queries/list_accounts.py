"""ListAccounts query (CQRS read side).

Returns the accounts owned by a given user, as lightweight projections. Used by
the UI to discover the authenticated user's account(s) after login.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Sequence
from uuid import UUID

from application.dto import AccountDTO


@dataclass(frozen=True, slots=True)
class ListAccountsQuery:
    """Input for the ListAccounts query."""

    owner_id: UUID


class AccountsReader(ABC):
    """Read port returning account projections for an owner."""

    @abstractmethod
    async def list_by_owner(self, owner_id: UUID) -> Sequence[AccountDTO]:
        raise NotImplementedError


class ListAccounts:
    """Return every account owned by a user."""

    def __init__(self, reader: AccountsReader) -> None:
        self._reader = reader

    async def execute(self, query: ListAccountsQuery) -> Sequence[AccountDTO]:
        return await self._reader.list_by_owner(query.owner_id)
