"""TransferMoney use case.

Moves money between two accounts, charging a transfer fee. The sender is debited
``amount + fee`` and the recipient is credited ``amount``; both balance updates
and both ledger entries (one DEBIT, one CREDIT) are persisted inside a single
atomic transaction, so there are never partial commits.
"""

from __future__ import annotations

from application.dto import TransferMoneyCommand, TransferResultDTO
from application.exceptions import AccountNotFoundError, SameAccountTransferError
from application.transaction import TransactionManager
from domain.repositories.account_repository import AccountRepository
from domain.repositories.transaction_repository import TransactionRepository
from domain.services.transfer_fee import calculate_transfer_fee
from domain.value_objects.account_number import AccountNumber
from domain.value_objects.money import Money


class TransferMoney:
    """Transfer funds from one account to another, applying the fee policy."""

    def __init__(
        self,
        accounts: AccountRepository,
        transactions: TransactionRepository,
        transaction_manager: TransactionManager,
    ) -> None:
        self._accounts = accounts
        self._transactions = transactions
        self._tx = transaction_manager

    async def execute(self, command: TransferMoneyCommand) -> TransferResultDTO:
        # 1-3. Load both parties and make sure they exist.
        sender = await self._accounts.get_by_id(command.from_account_id)
        if sender is None:
            raise AccountNotFoundError(
                f"Sender account not found: {command.from_account_id}"
            )

        recipient_number = AccountNumber(command.to_account_number)
        recipient = await self._accounts.get_by_number(recipient_number)
        if recipient is None:
            raise AccountNotFoundError(
                f"Recipient account not found: {command.to_account_number}"
            )

        if sender.id == recipient.id:
            raise SameAccountTransferError("Cannot transfer money to the same account")

        # 4. Compute the amount and the fee.
        amount = Money(command.amount, command.currency)
        fee = calculate_transfer_fee(amount)
        total = amount.add(fee)

        # 5-9. Move the money through the domain aggregates. ``withdraw`` enforces
        # sufficient funds and emits the DEBIT; ``deposit`` emits the CREDIT.
        debit = sender.withdraw(total)
        credit = recipient.deposit(amount)

        # 10. Persist everything atomically: no partial commits.
        async with self._tx.atomic():
            await self._accounts.update(sender)
            await self._accounts.update(recipient)
            await self._transactions.add(debit)
            await self._transactions.add(credit)

        return TransferResultDTO(
            from_account_number=str(sender.account_number),
            to_account_number=str(recipient.account_number),
            amount=amount.amount,
            fee=fee.amount,
            total_debited=total.amount,
            currency=amount.currency,
            from_balance=sender.balance.amount,
            to_balance=recipient.balance.amount,
        )
