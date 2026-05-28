from dataclasses import dataclass
from datetime import datetime


@dataclass
class Ticket:
    id: int | None
    title: str
    description: str
    category: str
    priority: str
    status: str
    requester: str
    assignee: str | None
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None


@dataclass
class Comment:
    id: int | None
    ticket_id: int
    author: str
    body: str
    created_at: datetime
