"""API endpoints (stages 6-9): register, login, balance, transactions.

Each async view resolves its use case/query from the dishka REQUEST scope and
translates DTOs to Ninja response schemas.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from dishka import Scope
from ninja import Query, Router

from application.dto import LoginCommand, RegisterUserCommand, TransferMoneyCommand
from application.queries.get_balance import GetBalance, GetBalanceQuery
from application.queries.list_accounts import ListAccounts, ListAccountsQuery
from application.queries.list_transactions import (
    ListTransactions,
    ListTransactionsQuery,
)
from application.usecases.login import Login
from application.usecases.register_user import RegisterUser
from application.usecases.transfer_money import TransferMoney
from infrastructure.django.api.auth import JWTAuth
from infrastructure.django.api.schemas import (
    AccountOut,
    BalanceOut,
    LoginIn,
    RegisterIn,
    TokenOut,
    TransactionOut,
    TransferIn,
    TransferOut,
    UserOut,
)
from infrastructure.django.di.container import container

router = Router()


@router.post("/auth/register", response={201: UserOut}, auth=None)
async def register(request, payload: RegisterIn):
    async with container(scope=Scope.REQUEST) as request_container:
        use_case = await request_container.get(RegisterUser)
        dto = await use_case.execute(
            RegisterUserCommand(email=payload.email, password=payload.password)
        )
    return 201, UserOut(
        id=dto.id,
        email=dto.email,
        account=AccountOut(
            id=dto.account.id,
            account_number=dto.account.account_number,
            balance=dto.account.balance,
            currency=dto.account.currency,
        ),
    )


@router.post("/auth/login", response=TokenOut, auth=None)
async def login(request, payload: LoginIn):
    async with container(scope=Scope.REQUEST) as request_container:
        use_case = await request_container.get(Login)
        dto = await use_case.execute(
            LoginCommand(email=payload.email, password=payload.password)
        )
    return TokenOut(access_token=dto.access_token, token_type=dto.token_type)


@router.get("/accounts", response=list[AccountOut], auth=JWTAuth())
async def list_accounts(request):
    owner_id = UUID(str(request.auth))
    async with container(scope=Scope.REQUEST) as request_container:
        query = await request_container.get(ListAccounts)
        items = await query.execute(ListAccountsQuery(owner_id=owner_id))
    return [
        AccountOut(
            id=item.id,
            account_number=item.account_number,
            balance=item.balance,
            currency=item.currency,
        )
        for item in items
    ]


@router.get(
    "/accounts/{account_id}/balance", response=BalanceOut, auth=JWTAuth()
)
async def get_balance(request, account_id: UUID):
    async with container(scope=Scope.REQUEST) as request_container:
        query = await request_container.get(GetBalance)
        dto = await query.execute(GetBalanceQuery(account_id=account_id))
    return BalanceOut(
        account_number=dto.account_number,
        balance=dto.balance,
        currency=dto.currency,
    )


@router.post(
    "/accounts/{account_id}/transfers", response=TransferOut, auth=JWTAuth()
)
async def transfer_money(request, account_id: UUID, payload: TransferIn):
    async with container(scope=Scope.REQUEST) as request_container:
        use_case = await request_container.get(TransferMoney)
        dto = await use_case.execute(
            TransferMoneyCommand(
                from_account_id=account_id,
                to_account_number=payload.to_account_number,
                amount=payload.amount,
                currency=payload.currency,
            )
        )
    return TransferOut(
        from_account_number=dto.from_account_number,
        to_account_number=dto.to_account_number,
        amount=dto.amount,
        fee=dto.fee,
        total_debited=dto.total_debited,
        currency=dto.currency,
        from_balance=dto.from_balance,
        to_balance=dto.to_balance,
    )


@router.get(
    "/accounts/{account_id}/transactions",
    response=list[TransactionOut],
    auth=JWTAuth(),
)
async def list_transactions(
    request,
    account_id: UUID,
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
):
    async with container(scope=Scope.REQUEST) as request_container:
        query = await request_container.get(ListTransactions)
        items = await query.execute(
            ListTransactionsQuery(
                account_id=account_id, date_from=date_from, date_to=date_to
            )
        )
    return [
        TransactionOut(
            amount=item.amount,
            currency=item.currency,
            type=item.type,
            created_at=item.created_at,
        )
        for item in items
    ]
