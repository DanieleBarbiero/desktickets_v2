from desktickets_v2.domain.errors import (
    ClosedTicketAssignmentError,
    InvalidStatusTransitionError,
    ValidationError,
)

ALLOWED_PRIORITIES = {"low", "medium", "high", "urgent"}
ALLOWED_STATUSES = {"open", "in_progress", "closed"}
ALLOWED_STATUS_TRANSITIONS = {
    "open": {"in_progress", "closed"},
    "in_progress": {"open", "closed"},
    "closed": set(),
}


def validate_required_text(field_name: str, value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValidationError(f"{field_name} is required")
    return cleaned


def validate_priority(priority: str) -> str:
    cleaned = validate_required_text("priority", priority).lower()
    if cleaned not in ALLOWED_PRIORITIES:
        allowed = ", ".join(sorted(ALLOWED_PRIORITIES))
        raise ValidationError(f"priority must be one of: {allowed}")
    return cleaned


def validate_status(status: str) -> str:
    cleaned = validate_required_text("status", status).lower()
    if cleaned not in ALLOWED_STATUSES:
        allowed = ", ".join(sorted(ALLOWED_STATUSES))
        raise ValidationError(f"status must be one of: {allowed}")
    return cleaned


def validate_status_transition(current_status: str, new_status: str) -> str:
    current = validate_status(current_status)
    new = validate_status(new_status)

    if new not in ALLOWED_STATUS_TRANSITIONS[current]:
        raise InvalidStatusTransitionError(
            f"cannot transition ticket status from {current} to {new}"
        )

    return new


def validate_assignee(assignee: str) -> str:
    return validate_required_text("assignee", assignee)


def ensure_ticket_can_change_assignee(current_status: str) -> None:
    status = validate_status(current_status)
    if status == "closed":
        raise ClosedTicketAssignmentError("cannot change assignee for a closed ticket")


def validate_comment_author(author: str) -> str:
    return validate_required_text("author", author)


def validate_comment_body(body: str) -> str:
    return validate_required_text("body", body)
