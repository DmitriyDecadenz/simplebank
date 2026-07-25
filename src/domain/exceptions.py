"""Domain-level errors.

These exceptions express violations of business rules and invariants.
They are intentionally free of any framework/ORM/transport concerns so the
domain layer stays isolated from infrastructure.
"""


class DomainError(Exception):
    """Base class for every domain rule violation."""


class InvalidEmailError(DomainError):
    """Raised when an email address does not have a valid format."""


class InvalidPasswordHashError(DomainError):
    """Raised when a password hash is empty or malformed."""


class InvalidAccountNumberError(DomainError):
    """Raised when an account number does not satisfy the required format."""


class InvalidMoneyError(DomainError):
    """Raised when a monetary amount cannot be constructed."""


class NegativeMoneyError(InvalidMoneyError):
    """Raised when a monetary amount is negative."""


class CurrencyMismatchError(DomainError):
    """Raised when two monetary amounts of different currencies are combined."""


class InvalidAmountError(DomainError):
    """Raised when a deposit/withdrawal amount is not strictly positive."""


class InsufficientFundsError(DomainError):
    """Raised when a withdrawal exceeds the available balance."""


class NegativeBalanceError(DomainError):
    """Raised when an account balance invariant (balance >= 0) is broken."""
