class DeskTicketsError(Exception):
    """Base application error."""


class ValidationError(DeskTicketsError):
    """Raised when user-provided data is invalid."""


class NotFoundError(DeskTicketsError):
    """Raised when a requested resource does not exist."""


class InvalidStatusTransitionError(ValidationError):
    """Raised when a status change is not allowed by domain rules."""


class ClosedTicketAssignmentError(ValidationError):
    """Raised when assignment is attempted on a closed ticket."""
