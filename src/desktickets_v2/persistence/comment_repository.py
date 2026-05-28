import sqlite3
from datetime import datetime

from desktickets_v2.domain.models import Comment


class CommentRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def create(self, comment: Comment) -> Comment:
        cursor = self._connection.execute(
            """
            INSERT INTO comments (ticket_id, author, body, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                comment.ticket_id,
                comment.author,
                comment.body,
                comment.created_at.isoformat(),
            ),
        )
        self._connection.commit()
        return Comment(
            id=int(cursor.lastrowid),
            ticket_id=comment.ticket_id,
            author=comment.author,
            body=comment.body,
            created_at=comment.created_at,
        )

    def list_by_ticket_id(self, *, ticket_id: int) -> list[Comment]:
        rows = self._connection.execute(
            """
            SELECT id, ticket_id, author, body, created_at
            FROM comments
            WHERE ticket_id = ?
            ORDER BY id ASC
            """,
            (ticket_id,),
        ).fetchall()

        comments: list[Comment] = []
        for row in rows:
            comments.append(
                Comment(
                    id=int(row["id"]),
                    ticket_id=int(row["ticket_id"]),
                    author=str(row["author"]),
                    body=str(row["body"]),
                    created_at=datetime.fromisoformat(str(row["created_at"])),
                )
            )

        return comments
