import sqlite3
from contextlib import closing
from datetime import datetime, timezone

from desktickets_v2.domain.models import Comment, Ticket
from desktickets_v2.persistence.comment_repository import CommentRepository
from desktickets_v2.persistence.schema import initialize_schema
from desktickets_v2.persistence.ticket_repository import TicketRepository


def test_create_and_get_ticket_roundtrip() -> None:
    with closing(sqlite3.connect(":memory:")) as connection:
        connection.row_factory = sqlite3.Row
        initialize_schema(connection)
        repository = TicketRepository(connection)

        now = datetime.now(timezone.utc)
        created = repository.create(
            Ticket(
                id=None,
                title="Laptop issue",
                description="Blue screen on startup",
                category="hardware",
                priority="high",
                status="open",
                requester="bob",
                assignee=None,
                created_at=now,
                updated_at=now,
                closed_at=None,
            )
        )

        loaded = repository.get_by_id(created.id or -1)
        assert loaded is not None
        assert loaded.title == "Laptop issue"
        assert loaded.status == "open"
        assert loaded.closed_at is None


def test_list_all_returns_tickets_in_id_order() -> None:
    with closing(sqlite3.connect(":memory:")) as connection:
        connection.row_factory = sqlite3.Row
        initialize_schema(connection)
        repository = TicketRepository(connection)

        now = datetime.now(timezone.utc)
        repository.create(
            Ticket(
                id=None,
                title="Second ticket",
                description="desc 2",
                category="software",
                priority="medium",
                status="open",
                requester="alice",
                assignee=None,
                created_at=now,
                updated_at=now,
                closed_at=None,
            )
        )
        repository.create(
            Ticket(
                id=None,
                title="Third ticket",
                description="desc 3",
                category="network",
                priority="low",
                status="open",
                requester="carol",
                assignee=None,
                created_at=now,
                updated_at=now,
                closed_at=None,
            )
        )

        tickets = repository.list_all()
        assert len(tickets) == 2
        assert tickets[0].id is not None
        assert tickets[1].id is not None
        assert tickets[0].id < tickets[1].id
        assert tickets[0].title == "Second ticket"
        assert tickets[1].title == "Third ticket"


def test_create_and_list_comments_for_ticket() -> None:
    with closing(sqlite3.connect(":memory:")) as connection:
        connection.row_factory = sqlite3.Row
        initialize_schema(connection)
        ticket_repository = TicketRepository(connection)
        comment_repository = CommentRepository(connection)

        now = datetime.now(timezone.utc)
        created_ticket = ticket_repository.create(
            Ticket(
                id=None,
                title="VPN issue",
                description="Fails to connect",
                category="network",
                priority="high",
                status="open",
                requester="alice",
                assignee=None,
                created_at=now,
                updated_at=now,
                closed_at=None,
            )
        )

        first_comment = comment_repository.create(
            Comment(
                id=None,
                ticket_id=created_ticket.id or -1,
                author="operator-a",
                body="Investigating issue",
                created_at=now,
            )
        )
        second_comment = comment_repository.create(
            Comment(
                id=None,
                ticket_id=created_ticket.id or -1,
                author="operator-b",
                body="Resolved with new VPN profile",
                created_at=now,
            )
        )

        comments = comment_repository.list_by_ticket_id(ticket_id=created_ticket.id or -1)
        assert [comment.id for comment in comments] == [first_comment.id, second_comment.id]
        assert comments[0].author == "operator-a"
        assert comments[1].body == "Resolved with new VPN profile"


def test_list_filtered_combines_multiple_filters() -> None:
    with closing(sqlite3.connect(":memory:")) as connection:
        connection.row_factory = sqlite3.Row
        initialize_schema(connection)
        repository = TicketRepository(connection)

        now = datetime.now(timezone.utc)
        repository.create(
            Ticket(
                id=None,
                title="VPN issue",
                description="Fails to connect",
                category="network",
                priority="high",
                status="open",
                requester="alice",
                assignee="operator-a",
                created_at=now,
                updated_at=now,
                closed_at=None,
            )
        )
        repository.create(
            Ticket(
                id=None,
                title="Printer issue",
                description="Paper jam",
                category="hardware",
                priority="high",
                status="open",
                requester="bob",
                assignee="operator-a",
                created_at=now,
                updated_at=now,
                closed_at=None,
            )
        )

        tickets = repository.list_filtered(status="open", priority="high", category="network")
        assert len(tickets) == 1
        assert tickets[0].title == "VPN issue"


def test_list_filtered_returns_empty_when_no_match() -> None:
    with closing(sqlite3.connect(":memory:")) as connection:
        connection.row_factory = sqlite3.Row
        initialize_schema(connection)
        repository = TicketRepository(connection)

        now = datetime.now(timezone.utc)
        repository.create(
            Ticket(
                id=None,
                title="Email issue",
                description="Cannot send mail",
                category="software",
                priority="medium",
                status="open",
                requester="alice",
                assignee=None,
                created_at=now,
                updated_at=now,
                closed_at=None,
            )
        )

        tickets = repository.list_filtered(assignee="operator-z")
        assert tickets == []
