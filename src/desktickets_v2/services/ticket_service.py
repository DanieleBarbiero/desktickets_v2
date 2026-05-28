from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from desktickets_v2.domain.errors import NotFoundError
from desktickets_v2.domain.models import Comment, Ticket
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
from desktickets_v2.persistence.comment_repository import CommentRepository
from desktickets_v2.persistence.ticket_repository import TicketRepository


@dataclass
class TicketDetail:
    ticket: Ticket
    comments: list[Comment]


class TicketService:
    def __init__(
        self,
        ticket_repository: TicketRepository,
        comment_repository: CommentRepository,
        *,
        close_callback: Callable[[], None] | None = None,
    ) -> None:
        self._ticket_repository = ticket_repository
        self._comment_repository = comment_repository
        self._close_callback = close_callback

    def create_ticket(
        self,
        *,
        title: str,
        description: str,
        category: str,
        priority: str,
        requester: str,
    ) -> Ticket:
        now = datetime.now(timezone.utc)

        ticket = Ticket(
            id=None,
            title=validate_required_text("title", title),
            description=validate_required_text("description", description),
            category=validate_required_text("category", category),
            priority=validate_priority(priority),
            status=validate_status("open"),
            requester=validate_required_text("requester", requester),
            assignee=None,
            created_at=now,
            updated_at=now,
            closed_at=None,
        )

        return self._ticket_repository.create(ticket)

    def list_tickets(
        self,
        *,
        status: str | None = None,
        priority: str | None = None,
        category: str | None = None,
        assignee: str | None = None,
    ) -> list[Ticket]:
        validated_status = validate_status(status) if status is not None else None
        validated_priority = validate_priority(priority) if priority is not None else None
        validated_category = (
            validate_required_text("category", category) if category is not None else None
        )
        validated_assignee = validate_assignee(assignee) if assignee is not None else None

        return self._ticket_repository.list_filtered(
            status=validated_status,
            priority=validated_priority,
            category=validated_category,
            assignee=validated_assignee,
        )

    def get_ticket_detail(self, *, ticket_id: int) -> TicketDetail:
        ticket = self._ticket_repository.get_by_id(ticket_id)
        if ticket is None:
            raise NotFoundError(f"Ticket with id {ticket_id} was not found")

        comments = self._comment_repository.list_by_ticket_id(ticket_id=ticket_id)
        return TicketDetail(ticket=ticket, comments=comments)

    def change_ticket_status(self, *, ticket_id: int, new_status: str) -> Ticket:
        ticket = self._ticket_repository.get_by_id(ticket_id)
        if ticket is None:
            raise NotFoundError(f"Ticket with id {ticket_id} was not found")

        next_status = validate_status_transition(ticket.status, new_status)
        now = datetime.now(timezone.utc)

        ticket.status = next_status
        ticket.updated_at = now
        if next_status == "closed":
            ticket.closed_at = now

        return self._ticket_repository.update(ticket)

    def assign_ticket(self, *, ticket_id: int, assignee: str) -> Ticket:
        ticket = self._ticket_repository.get_by_id(ticket_id)
        if ticket is None:
            raise NotFoundError(f"Ticket with id {ticket_id} was not found")

        ensure_ticket_can_change_assignee(ticket.status)

        ticket.assignee = validate_assignee(assignee)
        ticket.updated_at = datetime.now(timezone.utc)

        return self._ticket_repository.update(ticket)

    def add_comment(self, *, ticket_id: int, author: str, body: str) -> Comment:
        ticket = self._ticket_repository.get_by_id(ticket_id)
        if ticket is None:
            raise NotFoundError(f"Ticket with id {ticket_id} was not found")

        comment = Comment(
            id=None,
            ticket_id=ticket_id,
            author=validate_comment_author(author),
            body=validate_comment_body(body),
            created_at=datetime.now(timezone.utc),
        )
        return self._comment_repository.create(comment)

    def close(self) -> None:
        if self._close_callback is not None:
            self._close_callback()
