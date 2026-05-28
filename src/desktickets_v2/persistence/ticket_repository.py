import sqlite3
from datetime import datetime

from desktickets_v2.domain.models import Ticket


class TicketRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def create(self, ticket: Ticket) -> Ticket:
        cursor = self._connection.execute(
            """
            INSERT INTO tickets (
                title,
                description,
                category,
                priority,
                status,
                requester,
                assignee,
                created_at,
                updated_at,
                closed_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ticket.title,
                ticket.description,
                ticket.category,
                ticket.priority,
                ticket.status,
                ticket.requester,
                ticket.assignee,
                ticket.created_at.isoformat(),
                ticket.updated_at.isoformat(),
                ticket.closed_at.isoformat() if ticket.closed_at else None,
            ),
        )
        self._connection.commit()
        return Ticket(
            id=int(cursor.lastrowid),
            title=ticket.title,
            description=ticket.description,
            category=ticket.category,
            priority=ticket.priority,
            status=ticket.status,
            requester=ticket.requester,
            assignee=ticket.assignee,
            created_at=ticket.created_at,
            updated_at=ticket.updated_at,
            closed_at=ticket.closed_at,
        )

    def get_by_id(self, ticket_id: int) -> Ticket | None:
        row = self._connection.execute(
            """
            SELECT id, title, description, category, priority, status,
                   requester, assignee, created_at, updated_at, closed_at
            FROM tickets
            WHERE id = ?
            """,
            (ticket_id,),
        ).fetchone()

        if row is None:
            return None

        return Ticket(
            id=int(row["id"]),
            title=str(row["title"]),
            description=str(row["description"]),
            category=str(row["category"]),
            priority=str(row["priority"]),
            status=str(row["status"]),
            requester=str(row["requester"]),
            assignee=str(row["assignee"]) if row["assignee"] is not None else None,
            created_at=datetime.fromisoformat(str(row["created_at"])),
            updated_at=datetime.fromisoformat(str(row["updated_at"])),
            closed_at=datetime.fromisoformat(str(row["closed_at"])) if row["closed_at"] else None,
        )

    def list_all(self) -> list[Ticket]:
        return self.list_filtered()

    def list_filtered(
        self,
        *,
        status: str | None = None,
        priority: str | None = None,
        category: str | None = None,
        assignee: str | None = None,
    ) -> list[Ticket]:
        filters: list[str] = []
        params: list[str] = []

        if status is not None:
            filters.append("status = ?")
            params.append(status)
        if priority is not None:
            filters.append("priority = ?")
            params.append(priority)
        if category is not None:
            filters.append("category = ?")
            params.append(category)
        if assignee is not None:
            filters.append("assignee = ?")
            params.append(assignee)

        where_clause = ""
        if filters:
            where_clause = "WHERE " + " AND ".join(filters)

        rows = self._connection.execute(
            f"""
            SELECT id, title, description, category, priority, status,
                   requester, assignee, created_at, updated_at, closed_at
            FROM tickets
            {where_clause}
            ORDER BY id ASC
            """,
            params,
        ).fetchall()

        tickets: list[Ticket] = []
        for row in rows:
            tickets.append(
                Ticket(
                    id=int(row["id"]),
                    title=str(row["title"]),
                    description=str(row["description"]),
                    category=str(row["category"]),
                    priority=str(row["priority"]),
                    status=str(row["status"]),
                    requester=str(row["requester"]),
                    assignee=str(row["assignee"]) if row["assignee"] is not None else None,
                    created_at=datetime.fromisoformat(str(row["created_at"])),
                    updated_at=datetime.fromisoformat(str(row["updated_at"])),
                    closed_at=datetime.fromisoformat(str(row["closed_at"])) if row["closed_at"] else None,
                )
            )

        return tickets

    def update(self, ticket: Ticket) -> Ticket:
        self._connection.execute(
            """
            UPDATE tickets
            SET title = ?,
                description = ?,
                category = ?,
                priority = ?,
                status = ?,
                requester = ?,
                assignee = ?,
                updated_at = ?,
                closed_at = ?
            WHERE id = ?
            """,
            (
                ticket.title,
                ticket.description,
                ticket.category,
                ticket.priority,
                ticket.status,
                ticket.requester,
                ticket.assignee,
                ticket.updated_at.isoformat(),
                ticket.closed_at.isoformat() if ticket.closed_at else None,
                ticket.id,
            ),
        )
        self._connection.commit()
        return ticket
