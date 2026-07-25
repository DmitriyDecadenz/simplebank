"""Application-level errors.

These represent failures of use-case orchestration (e.g. uniqueness checks that
require a repository) as opposed to pure domain invariant violations.
"""


class ApplicationError(Exception):
    """Base class for application-layer errors."""


class EmailAlreadyExistsError(ApplicationError):
    """Raised when registering with an email that is already taken."""


class AccountNumberGenerationError(ApplicationError):
    """Raised when a unique account number could not be generated."""


class InvalidCredentialsError(ApplicationError):
    """Raised when authentication fails (unknown email or wrong password).

    Intentionally does not disclose which of the two failed to avoid user
    enumeration.
    """
