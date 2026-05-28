import argparse
from datetime import date, datetime, time

from desktickets_v2.app import build_ticket_service
from desktickets_v2.domain.errors import NotFoundError, ValidationError


NONE_VALUE = "-"
LIST_HEADER = "ID | TITLE | STATUS | PRIORITY | CATEGORY | ASSIGNEE | CREATED_AT"


def _exit_with_error(parser: argparse.ArgumentParser, exc: Exception) -> None:
    parser.exit(2, f"Error: {exc}\n")


def _optional_text(value: str | None) -> str:
    return value if value is not None else NONE_VALUE


def _optional_datetime_iso(value: date | datetime | time | None) -> str:
    if value is None:
        return NONE_VALUE
    return value.isoformat()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="desktickets_v2")
    parser.add_argument("--db-path", default="desktickets.db")

    subparsers = parser.add_subparsers(dest="command", required=True)
    create_parser = subparsers.add_parser("create-ticket", help="Create a new ticket")
    create_parser.add_argument("--title", required=True)
    create_parser.add_argument("--description", required=True)
    create_parser.add_argument("--category", required=True)
    create_parser.add_argument("--priority", required=True)
    create_parser.add_argument("--requester", required=True)

    list_parser = subparsers.add_parser("list-tickets", help="List existing tickets")
    list_parser.add_argument("--status")
    list_parser.add_argument("--priority")
    list_parser.add_argument("--category")
    list_parser.add_argument("--assignee")

    show_parser = subparsers.add_parser("show-ticket", help="Show ticket detail")
    show_parser.add_argument("--id", type=int, required=True)

    status_parser = subparsers.add_parser("change-status", help="Change ticket status")
    status_parser.add_argument("--id", type=int, required=True)
    status_parser.add_argument("--status", required=True)

    assign_parser = subparsers.add_parser("assign-ticket", help="Assign ticket to an assignee")
    assign_parser.add_argument("--id", type=int, required=True)
    assign_parser.add_argument("--assignee", required=True)

    comment_parser = subparsers.add_parser("add-comment", help="Add a comment to a ticket")
    comment_parser.add_argument("--id", type=int, required=True)
    comment_parser.add_argument("--author", required=True)
    comment_parser.add_argument("--body", required=True)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    service = build_ticket_service(db_path=args.db_path)
    ticket = None
    tickets = None
    detail = None
    comment = None
    try:
        if args.command == "create-ticket":
            try:
                ticket = service.create_ticket(
                    title=args.title,
                    description=args.description,
                    category=args.category,
                    priority=args.priority,
                    requester=args.requester,
                )
            except ValidationError as exc:
                _exit_with_error(parser, exc)

            print(f"OK: ticket created (id={ticket.id})")
            return 0

        if args.command == "list-tickets":
            try:
                tickets = service.list_tickets(
                    status=args.status,
                    priority=args.priority,
                    category=args.category,
                    assignee=args.assignee,
                )
            except ValidationError as exc:
                _exit_with_error(parser, exc)

            if not tickets:
                print("No tickets found.")
                return 0

            print(LIST_HEADER)
            for ticket in tickets:
                print(
                    f"{ticket.id} | {ticket.title} | {ticket.status} | "
                    f"{ticket.priority} | {ticket.category} | {_optional_text(ticket.assignee)} | "
                    f"{ticket.created_at.isoformat()}"
                )
            return 0

        if args.command == "show-ticket":
            try:
                detail = service.get_ticket_detail(ticket_id=args.id)
            except NotFoundError as exc:
                _exit_with_error(parser, exc)

            ticket = detail.ticket
            print("Ticket")
            print(f"  id: {ticket.id}")
            print(f"  title: {ticket.title}")
            print(f"  description: {ticket.description}")
            print(f"  status: {ticket.status}")
            print(f"  priority: {ticket.priority}")
            print(f"  category: {ticket.category}")
            print(f"  requester: {ticket.requester}")
            print(f"  assignee: {_optional_text(ticket.assignee)}")
            print(f"  created_at: {ticket.created_at.isoformat()}")
            print(f"  updated_at: {ticket.updated_at.isoformat()}")
            print(f"  closed_at: {_optional_datetime_iso(ticket.closed_at)}")
            print("Comments")
            if not detail.comments:
                print("  - none")
            else:
                for comment in detail.comments:
                    print(f"  - {comment.created_at.isoformat()} | {comment.author}: {comment.body}")
            return 0

        if args.command == "change-status":
            try:
                ticket = service.change_ticket_status(ticket_id=args.id, new_status=args.status)
            except (NotFoundError, ValidationError) as exc:
                _exit_with_error(parser, exc)

            print(f"OK: ticket {ticket.id} status updated to {ticket.status}")
            return 0

        if args.command == "assign-ticket":
            try:
                ticket = service.assign_ticket(ticket_id=args.id, assignee=args.assignee)
            except (NotFoundError, ValidationError) as exc:
                _exit_with_error(parser, exc)

            print(f"OK: ticket {ticket.id} assigned to {ticket.assignee}")
            return 0

        if args.command == "add-comment":
            try:
                comment = service.add_comment(ticket_id=args.id, author=args.author, body=args.body)
            except (NotFoundError, ValidationError) as exc:
                _exit_with_error(parser, exc)

            print(f"OK: comment added to ticket {comment.ticket_id}")
            return 0

        parser.exit(2, "Unknown command\n")
    finally:
        service.close()


if __name__ == "__main__":
    raise SystemExit(main())
