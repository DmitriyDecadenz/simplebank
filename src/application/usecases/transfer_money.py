"""TransferMoney use case.

Moves money between two accounts, charging a transfer fee. The whole critical
section (load both accounts, check funds, debit/credit, persist) runs inside a
single database transaction with row locks, so concurrent transfers on the same
account cannot cause lost updates or overdrafts.
"""

from __future__ import annotations

from application.dto import TransferMoneyCommand, TransferResultDTO
from application.exceptions import AccountNotFoundError, SameAccountTransferError
from application.transaction import AtomicContext, TransactionManager
from domain.services.transfer import make_transfer
from domain.value_objects.account_number import AccountNumber
from domain.value_objects.money import Money


class TransferMoney:
    """Transfer funds from one account to another, applying the fee policy."""

    def __init__(self, transaction_manager: TransactionManager) -> None:
        self._tx = transaction_manager

    async def execute(self, command: TransferMoneyCommand) -> TransferResultDTO:
        recipient_number = AccountNumber(command.to_account_number)
        amount = Money(command.amount, command.currency)

        def work(ctx: AtomicContext) -> TransferResultDTO:
            # Resolve the recipient by its immutable number (no lock needed).
            recipient_id = ctx.find_account_id_by_number(recipient_number)
            if recipient_id is None:
                raise AccountNotFoundError(
                    f"Recipient account not found: {command.to_account_number}"
                )
            if recipient_id == command.from_account_id:
                raise SameAccountTransferError(
                    "Cannot transfer money to the same account"
                )

            # Lock both rows in a deterministic order to avoid deadlocks between
            # concurrent transfers (A->B and B->A).
            locked = {
                account_id: ctx.get_account_for_update(account_id)
                for account_id in sorted(
                    {command.from_account_id, recipient_id}, key=str
                )
            }

            sender = locked[command.from_account_id]
            if sender is None:
                raise AccountNotFoundError(
                    f"Sender account not found: {command.from_account_id}"
                )
            recipient = locked[recipient_id]
            if recipient is None:
                raise AccountNotFoundError(
                    f"Recipient account not found: {command.to_account_number}"
                )

            # Domain performs the money movement (enforces sufficient funds).
            entries = make_transfer(sender, recipient, amount)

            ctx.save_account(sender)
            ctx.save_account(recipient)
            ctx.add_transaction(entries.debit)
            ctx.add_transaction(entries.credit)

            return TransferResultDTO(
                from_account_number=str(sender.account_number),
                to_account_number=str(recipient.account_number),
                amount=amount.amount,
                fee=entries.fee.amount,
                total_debited=entries.total.amount,
                currency=amount.currency,
                from_balance=sender.balance.amount,
                to_balance=recipient.balance.amount,
            )

        return await self._tx.run(work)
