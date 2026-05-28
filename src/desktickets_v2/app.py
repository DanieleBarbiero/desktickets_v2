from desktickets_v2.persistence.comment_repository import CommentRepository
from desktickets_v2.persistence.db import open_connection
from desktickets_v2.persistence.schema import initialize_schema
from desktickets_v2.persistence.ticket_repository import TicketRepository
from desktickets_v2.services.ticket_service import TicketService


DEFAULT_DB_PATH = "desktickets.db"


def build_ticket_service(db_path: str = DEFAULT_DB_PATH) -> TicketService:
    connection = open_connection(db_path)
    initialize_schema(connection)
    ticket_repository = TicketRepository(connection)
    comment_repository = CommentRepository(connection)
    return TicketService(
        ticket_repository,
        comment_repository,
        close_callback=connection.close,
    )
