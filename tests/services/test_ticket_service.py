import sqlite3
from collections.abc import Generator

import pytest

from desktickets_v2.domain.errors import (
    ClosedTicketAssignmentError,
    InvalidStatusTransitionError,
    NotFoundError,
    ValidationError,
)
from desktickets_v2.persistence.comment_repository import CommentRepository
from desktickets_v2.persistence.schema import initialize_schema
from desktickets_v2.persistence.ticket_repository import TicketRepository
from desktickets_v2.services.ticket_service import TicketService


@pytest.fixture
def service() -> Generator[TicketService]:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    initialize_schema(connection)
    ticket_repository = TicketRepository(connection)
    comment_repository = CommentRepository(connection)
    ticket_service = TicketService(ticket_repository, comment_repository)
    try:
        yield ticket_service
    finally:
        connection.close()


def test_create_ticket_sets_open_status_and_closed_at_none(service: TicketService) -> None:
    ticket = service.create_ticket(
        title="VPN not working",
        description="Cannot access VPN from home",
        category="network",
        priority="medium",
        requester="alice",
    )

    assert ticket.id is not None
    assert ticket.status == "open"
    assert ticket.closed_at is None


def test_create_ticket_rejects_missing_required_field(service: TicketService) -> None:
    with pytest.raises(ValidationError, match="title is required"):
        service.create_ticket(
            title=" ",
            description="desc",
            category="network",
            priority="medium",
            requester="alice",
        )


def test_list_tickets_returns_created_tickets(service: TicketService) -> None:
    service.create_ticket(
        title="VPN not working",
        description="Cannot access VPN from home",
        category="network",
        priority="medium",
        requester="alice",
    )
    service.create_ticket(
        title="Printer issue",
        description="Paper jam",
        category="hardware",
        priority="low",
        requester="bob",
    )

    tickets = service.list_tickets()
    assert len(tickets) == 2
    assert tickets[0].title == "VPN not working"
    assert tickets[1].title == "Printer issue"


def test_get_ticket_detail_returns_ticket(service: TicketService) -> None:
    created = service.create_ticket(
        title="Monitor flickers",
        description="Screen flickers every hour",
        category="hardware",
        priority="high",
        requester="alice",
    )

    loaded = service.get_ticket_detail(ticket_id=created.id or -1)
    assert loaded.ticket.id == created.id
    assert loaded.ticket.description == "Screen flickers every hour"


def test_get_ticket_detail_raises_not_found(service: TicketService) -> None:
    with pytest.raises(NotFoundError, match="Ticket with id 999 was not found"):
        service.get_ticket_detail(ticket_id=999)


def test_change_ticket_status_to_in_progress_updates_status_and_updated_at(
    service: TicketService,
) -> None:
    created = service.create_ticket(
        title="Slow laptop",
        description="Takes 10 minutes to boot",
        category="hardware",
        priority="medium",
        requester="luca",
    )

    updated = service.change_ticket_status(ticket_id=created.id or -1, new_status="in_progress")
    assert updated.status == "in_progress"
    assert updated.closed_at is None
    assert updated.updated_at >= created.updated_at


def test_change_ticket_status_to_closed_sets_closed_at(service: TicketService) -> None:
    created = service.create_ticket(
        title="VPN issue",
        description="Cannot connect from home",
        category="network",
        priority="high",
        requester="sara",
    )

    closed = service.change_ticket_status(ticket_id=created.id or -1, new_status="closed")
    assert closed.status == "closed"
    assert closed.closed_at is not None
    assert closed.updated_at == closed.closed_at


def test_change_ticket_status_rejects_invalid_status(service: TicketService) -> None:
    created = service.create_ticket(
        title="Printer issue",
        description="Paper jam",
        category="hardware",
        priority="low",
        requester="mario",
    )

    with pytest.raises(ValidationError, match="status must be one of"):
        service.change_ticket_status(ticket_id=created.id or -1, new_status="done")


def test_change_ticket_status_rejects_invalid_transition(service: TicketService) -> None:
    created = service.create_ticket(
        title="Software install",
        description="Need new tool",
        category="software",
        priority="medium",
        requester="anna",
    )
    closed = service.change_ticket_status(ticket_id=created.id or -1, new_status="closed")

    with pytest.raises(
        InvalidStatusTransitionError,
        match="cannot transition ticket status from closed to open",
    ):
        service.change_ticket_status(ticket_id=closed.id or -1, new_status="open")


def test_change_ticket_status_raises_not_found(service: TicketService) -> None:
    with pytest.raises(NotFoundError, match="Ticket with id 999 was not found"):
        service.change_ticket_status(ticket_id=999, new_status="closed")


def test_assign_ticket_updates_assignee_and_updated_at(service: TicketService) -> None:
    created = service.create_ticket(
        title="Keyboard broken",
        description="Some keys do not respond",
        category="hardware",
        priority="medium",
        requester="marta",
    )

    updated = service.assign_ticket(ticket_id=created.id or -1, assignee="operator-a")

    assert updated.assignee == "operator-a"
    assert updated.updated_at >= created.updated_at


def test_assign_ticket_rejects_empty_assignee(service: TicketService) -> None:
    created = service.create_ticket(
        title="Permissions issue",
        description="Cannot access folder",
        category="access",
        priority="high",
        requester="leo",
    )

    with pytest.raises(ValidationError, match="assignee is required"):
        service.assign_ticket(ticket_id=created.id or -1, assignee="  ")


def test_assign_ticket_rejects_closed_ticket(service: TicketService) -> None:
    created = service.create_ticket(
        title="VPN issue",
        description="Cannot connect from office",
        category="network",
        priority="low",
        requester="paola",
    )
    closed = service.change_ticket_status(ticket_id=created.id or -1, new_status="closed")

    with pytest.raises(
        ClosedTicketAssignmentError,
        match="cannot change assignee for a closed ticket",
    ):
        service.assign_ticket(ticket_id=closed.id or -1, assignee="operator-b")


def test_assign_ticket_raises_not_found(service: TicketService) -> None:
    with pytest.raises(NotFoundError, match="Ticket with id 999 was not found"):
        service.assign_ticket(ticket_id=999, assignee="operator-c")


def test_add_comment_creates_comment_for_ticket(service: TicketService) -> None:
    created = service.create_ticket(
        title="VPN issue",
        description="Cannot connect from office",
        category="network",
        priority="medium",
        requester="mario",
    )

    comment = service.add_comment(
        ticket_id=created.id or -1,
        author="operator-a",
        body="Checking logs",
    )

    assert comment.id is not None
    assert comment.ticket_id == created.id
    assert comment.author == "operator-a"


def test_add_comment_rejects_blank_author(service: TicketService) -> None:
    created = service.create_ticket(
        title="VPN issue",
        description="Cannot connect from office",
        category="network",
        priority="medium",
        requester="mario",
    )

    with pytest.raises(ValidationError, match="author is required"):
        service.add_comment(ticket_id=created.id or -1, author=" ", body="Checking logs")


def test_add_comment_rejects_blank_body(service: TicketService) -> None:
    created = service.create_ticket(
        title="VPN issue",
        description="Cannot connect from office",
        category="network",
        priority="medium",
        requester="mario",
    )

    with pytest.raises(ValidationError, match="body is required"):
        service.add_comment(ticket_id=created.id or -1, author="operator-a", body=" ")


def test_add_comment_allows_closed_ticket(service: TicketService) -> None:
    created = service.create_ticket(
        title="Email issue",
        description="Mailbox quota exceeded",
        category="software",
        priority="low",
        requester="anna",
    )
    closed = service.change_ticket_status(ticket_id=created.id or -1, new_status="closed")

    comment = service.add_comment(
        ticket_id=closed.id or -1,
        author="operator-b",
        body="Post-closure note",
    )

    assert comment.ticket_id == closed.id


def test_add_comment_raises_not_found_for_missing_ticket(service: TicketService) -> None:
    with pytest.raises(NotFoundError, match="Ticket with id 999 was not found"):
        service.add_comment(ticket_id=999, author="operator-a", body="hello")


def test_get_ticket_detail_includes_comments(service: TicketService) -> None:
    created = service.create_ticket(
        title="Browser issue",
        description="Cannot open intranet",
        category="software",
        priority="high",
        requester="luca",
    )

    service.add_comment(ticket_id=created.id or -1, author="operator-a", body="Investigating")
    service.add_comment(ticket_id=created.id or -1, author="operator-b", body="Fixed")

    detail = service.get_ticket_detail(ticket_id=created.id or -1)
    assert len(detail.comments) == 2
    assert detail.comments[0].author == "operator-a"
    assert detail.comments[1].body == "Fixed"


def test_list_tickets_supports_combined_filters(service: TicketService) -> None:
    first = service.create_ticket(
        title="VPN issue",
        description="Cannot connect",
        category="network",
        priority="high",
        requester="alice",
    )
    second = service.create_ticket(
        title="Printer issue",
        description="Paper jam",
        category="hardware",
        priority="high",
        requester="bob",
    )
    service.assign_ticket(ticket_id=first.id or -1, assignee="operator-a")
    service.assign_ticket(ticket_id=second.id or -1, assignee="operator-a")

    tickets = service.list_tickets(
        status="open",
        priority="high",
        category="network",
        assignee="operator-a",
    )
    assert len(tickets) == 1
    assert tickets[0].title == "VPN issue"


def test_list_tickets_returns_empty_when_filter_has_no_match(service: TicketService) -> None:
    service.create_ticket(
        title="Email issue",
        description="Cannot send mail",
        category="software",
        priority="medium",
        requester="mario",
    )

    tickets = service.list_tickets(assignee="nobody")
    assert tickets == []


def test_list_tickets_rejects_invalid_status_filter(service: TicketService) -> None:
    with pytest.raises(ValidationError, match="status must be one of"):
        service.list_tickets(status="done")


def test_list_tickets_rejects_invalid_priority_filter(service: TicketService) -> None:
    with pytest.raises(ValidationError, match="priority must be one of"):
        service.list_tickets(priority="critical")
