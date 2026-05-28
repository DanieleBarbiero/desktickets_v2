import pytest

from desktickets_v2.domain.errors import (
    ClosedTicketAssignmentError,
    InvalidStatusTransitionError,
    ValidationError,
)
from desktickets_v2.domain.rules import (
    ensure_ticket_can_change_assignee,
    validate_assignee,
    validate_comment_author,
    validate_comment_body,
    validate_priority,
    validate_required_text,
    validate_status,
    validate_status_transition,
)


def test_validate_required_text_rejects_blank() -> None:
    with pytest.raises(ValidationError, match="title is required"):
        validate_required_text("title", "   ")


def test_validate_priority_accepts_allowed_values() -> None:
    assert validate_priority("HIGH") == "high"


def test_validate_priority_rejects_invalid_value() -> None:
    with pytest.raises(ValidationError, match="priority must be one of"):
        validate_priority("critical")


def test_validate_status_rejects_invalid_value() -> None:
    with pytest.raises(ValidationError, match="status must be one of"):
        validate_status("done")


def test_validate_status_transition_accepts_open_to_in_progress() -> None:
    assert validate_status_transition("open", "in_progress") == "in_progress"


def test_validate_status_transition_rejects_closed_to_open() -> None:
    with pytest.raises(
        InvalidStatusTransitionError,
        match="cannot transition ticket status from closed to open",
    ):
        validate_status_transition("closed", "open")


def test_validate_assignee_rejects_blank_value() -> None:
    with pytest.raises(ValidationError, match="assignee is required"):
        validate_assignee("   ")


def test_ensure_ticket_can_change_assignee_rejects_closed_ticket() -> None:
    with pytest.raises(
        ClosedTicketAssignmentError,
        match="cannot change assignee for a closed ticket",
    ):
        ensure_ticket_can_change_assignee("closed")


def test_validate_comment_author_rejects_blank_value() -> None:
    with pytest.raises(ValidationError, match="author is required"):
        validate_comment_author("  ")


def test_validate_comment_body_rejects_blank_value() -> None:
    with pytest.raises(ValidationError, match="body is required"):
        validate_comment_body("  ")
