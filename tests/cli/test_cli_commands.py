from pathlib import Path

import pytest

from desktickets_v2.cli import main
from desktickets_v2.persistence.db import open_connection


def test_create_ticket_command_persists_ticket(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    db_path = tmp_path / "desk.db"

    exit_code = main(
        [
            "--db-path",
            str(db_path),
            "create-ticket",
            "--title",
            "Email broken",
            "--description",
            "Cannot send emails",
            "--category",
            "software",
            "--priority",
            "high",
            "--requester",
            "mario",
        ]
    )

    assert exit_code == 0
    output = capsys.readouterr().out
    assert output.strip() == "OK: ticket created (id=1)"

    connection = open_connection(str(db_path))
    row = connection.execute("SELECT status, closed_at FROM tickets").fetchone()
    connection.close()
    assert row is not None
    assert row["status"] == "open"
    assert row["closed_at"] is None


def test_create_ticket_command_shows_readable_error(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    db_path = tmp_path / "desk.db"

    with pytest.raises(SystemExit) as exc_info:
        main(
            [
                "--db-path",
                str(db_path),
                "create-ticket",
                "--title",
                "",
                "--description",
                "Cannot send emails",
                "--category",
                "software",
                "--priority",
                "invalid-priority",
                "--requester",
                "mario",
            ]
        )

    assert exc_info.value.code == 2
    error_output = capsys.readouterr().err
    assert error_output.startswith("Error: ")


def test_list_tickets_command_shows_expected_fields(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    db_path = tmp_path / "desk.db"
    main(
        [
            "--db-path",
            str(db_path),
            "create-ticket",
            "--title",
            "Email broken",
            "--description",
            "Cannot send emails",
            "--category",
            "software",
            "--priority",
            "high",
            "--requester",
            "mario",
        ]
    )

    exit_code = main(["--db-path", str(db_path), "list-tickets"])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "ID | TITLE | STATUS | PRIORITY | CATEGORY | ASSIGNEE | CREATED_AT" in output
    assert "Email broken" in output
    assert "open" in output
    assert "high" in output
    assert "software" in output
    assert " - " in output or "| - |" in output


def test_show_ticket_command_prints_ticket_detail(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    db_path = tmp_path / "desk.db"
    main(
        [
            "--db-path",
            str(db_path),
            "create-ticket",
            "--title",
            "VPN down",
            "--description",
            "Cannot connect",
            "--category",
            "network",
            "--priority",
            "medium",
            "--requester",
            "anna",
        ]
    )

    exit_code = main(["--db-path", str(db_path), "show-ticket", "--id", "1"])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "Ticket" in output
    assert "id: 1" in output
    assert "title: VPN down" in output
    assert "description: Cannot connect" in output
    assert "status: open" in output
    assert "priority: medium" in output
    assert "category: network" in output
    assert "requester: anna" in output
    assert "Comments" in output


def test_show_ticket_command_returns_readable_not_found_error(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    db_path = tmp_path / "desk.db"

    with pytest.raises(SystemExit) as exc_info:
        main(["--db-path", str(db_path), "show-ticket", "--id", "123"])

    assert exc_info.value.code == 2
    error_output = capsys.readouterr().err
    assert error_output.startswith("Error: ")


def test_change_status_command_updates_ticket_status(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    db_path = tmp_path / "desk.db"
    main(
        [
            "--db-path",
            str(db_path),
            "create-ticket",
            "--title",
            "VPN down",
            "--description",
            "Cannot connect",
            "--category",
            "network",
            "--priority",
            "medium",
            "--requester",
            "anna",
        ]
    )
    capsys.readouterr()

    exit_code = main(["--db-path", str(db_path), "change-status", "--id", "1", "--status", "closed"])
    assert exit_code == 0

    output = capsys.readouterr().out
    assert output.strip() == "OK: ticket 1 status updated to closed"

    connection = open_connection(str(db_path))
    row = connection.execute("SELECT status, closed_at FROM tickets WHERE id = 1").fetchone()
    connection.close()
    assert row is not None
    assert row["status"] == "closed"
    assert row["closed_at"] is not None


def test_change_status_command_returns_readable_error_for_invalid_transition(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    db_path = tmp_path / "desk.db"
    main(
        [
            "--db-path",
            str(db_path),
            "create-ticket",
            "--title",
            "Printer down",
            "--description",
            "No response",
            "--category",
            "hardware",
            "--priority",
            "high",
            "--requester",
            "anna",
        ]
    )
    main(["--db-path", str(db_path), "change-status", "--id", "1", "--status", "closed"])

    with pytest.raises(SystemExit) as exc_info:
        main(["--db-path", str(db_path), "change-status", "--id", "1", "--status", "open"])

    assert exc_info.value.code == 2
    error_output = capsys.readouterr().err
    assert error_output.startswith("Error: ")


def test_assign_ticket_command_updates_assignee(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    db_path = tmp_path / "desk.db"
    main(
        [
            "--db-path",
            str(db_path),
            "create-ticket",
            "--title",
            "Email broken",
            "--description",
            "Cannot send emails",
            "--category",
            "software",
            "--priority",
            "high",
            "--requester",
            "mario",
        ]
    )
    capsys.readouterr()

    exit_code = main(
        ["--db-path", str(db_path), "assign-ticket", "--id", "1", "--assignee", "operator-a"]
    )

    assert exit_code == 0
    output = capsys.readouterr().out
    assert output.strip() == "OK: ticket 1 assigned to operator-a"

    connection = open_connection(str(db_path))
    row = connection.execute("SELECT assignee FROM tickets WHERE id = 1").fetchone()
    connection.close()
    assert row is not None
    assert row["assignee"] == "operator-a"


def test_assign_ticket_command_returns_readable_error_for_closed_ticket(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    db_path = tmp_path / "desk.db"
    main(
        [
            "--db-path",
            str(db_path),
            "create-ticket",
            "--title",
            "Printer down",
            "--description",
            "No response",
            "--category",
            "hardware",
            "--priority",
            "high",
            "--requester",
            "anna",
        ]
    )
    main(["--db-path", str(db_path), "change-status", "--id", "1", "--status", "closed"])

    with pytest.raises(SystemExit) as exc_info:
        main(
            ["--db-path", str(db_path), "assign-ticket", "--id", "1", "--assignee", "operator-b"]
        )

    assert exc_info.value.code == 2
    error_output = capsys.readouterr().err
    assert error_output.startswith("Error: ")


def test_assign_ticket_command_returns_readable_error_for_invalid_assignee(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    db_path = tmp_path / "desk.db"
    main(
        [
            "--db-path",
            str(db_path),
            "create-ticket",
            "--title",
            "VPN down",
            "--description",
            "Cannot connect",
            "--category",
            "network",
            "--priority",
            "medium",
            "--requester",
            "anna",
        ]
    )

    with pytest.raises(SystemExit) as exc_info:
        main(["--db-path", str(db_path), "assign-ticket", "--id", "1", "--assignee", "   "])

    assert exc_info.value.code == 2
    error_output = capsys.readouterr().err
    assert error_output.startswith("Error: ")


def test_add_comment_command_creates_comment_and_show_ticket_includes_it(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    db_path = tmp_path / "desk.db"
    main(
        [
            "--db-path",
            str(db_path),
            "create-ticket",
            "--title",
            "VPN down",
            "--description",
            "Cannot connect",
            "--category",
            "network",
            "--priority",
            "medium",
            "--requester",
            "anna",
        ]
    )
    capsys.readouterr()

    exit_code = main(
        [
            "--db-path",
            str(db_path),
            "add-comment",
            "--id",
            "1",
            "--author",
            "operator-a",
            "--body",
            "Checking VPN gateway",
        ]
    )

    assert exit_code == 0
    output = capsys.readouterr().out
    assert output.strip() == "OK: comment added to ticket 1"

    main(["--db-path", str(db_path), "show-ticket", "--id", "1"])
    detail_output = capsys.readouterr().out
    assert "Comments" in detail_output
    assert "operator-a: Checking VPN gateway" in detail_output


def test_add_comment_command_returns_readable_error_for_missing_ticket(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    db_path = tmp_path / "desk.db"

    with pytest.raises(SystemExit) as exc_info:
        main(
            [
                "--db-path",
                str(db_path),
                "add-comment",
                "--id",
                "123",
                "--author",
                "operator-a",
                "--body",
                "Any update?",
            ]
        )

    assert exc_info.value.code == 2
    error_output = capsys.readouterr().err
    assert error_output.startswith("Error: ")


def test_add_comment_command_returns_readable_error_for_invalid_fields(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    db_path = tmp_path / "desk.db"
    main(
        [
            "--db-path",
            str(db_path),
            "create-ticket",
            "--title",
            "VPN down",
            "--description",
            "Cannot connect",
            "--category",
            "network",
            "--priority",
            "medium",
            "--requester",
            "anna",
        ]
    )

    with pytest.raises(SystemExit) as exc_info:
        main(
            [
                "--db-path",
                str(db_path),
                "add-comment",
                "--id",
                "1",
                "--author",
                "   ",
                "--body",
                "   ",
            ]
        )

    assert exc_info.value.code == 2
    error_output = capsys.readouterr().err
    assert error_output.startswith("Error: ")


def test_list_tickets_command_applies_combined_filters(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    db_path = tmp_path / "desk.db"
    main(
        [
            "--db-path",
            str(db_path),
            "create-ticket",
            "--title",
            "VPN down",
            "--description",
            "Cannot connect",
            "--category",
            "network",
            "--priority",
            "high",
            "--requester",
            "anna",
        ]
    )
    main(
        [
            "--db-path",
            str(db_path),
            "create-ticket",
            "--title",
            "Printer down",
            "--description",
            "No response",
            "--category",
            "hardware",
            "--priority",
            "high",
            "--requester",
            "mario",
        ]
    )
    main(["--db-path", str(db_path), "assign-ticket", "--id", "1", "--assignee", "operator-a"])
    main(["--db-path", str(db_path), "assign-ticket", "--id", "2", "--assignee", "operator-a"])
    capsys.readouterr()

    exit_code = main(
        [
            "--db-path",
            str(db_path),
            "list-tickets",
            "--status",
            "open",
            "--priority",
            "high",
            "--category",
            "network",
            "--assignee",
            "operator-a",
        ]
    )

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "VPN down" in output
    assert "Printer down" not in output


def test_list_tickets_command_returns_empty_message_when_no_match(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    db_path = tmp_path / "desk.db"
    main(
        [
            "--db-path",
            str(db_path),
            "create-ticket",
            "--title",
            "Email broken",
            "--description",
            "Cannot send emails",
            "--category",
            "software",
            "--priority",
            "high",
            "--requester",
            "mario",
        ]
    )
    capsys.readouterr()

    exit_code = main(["--db-path", str(db_path), "list-tickets", "--assignee", "nobody"])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert output.strip() == "No tickets found."


def test_list_tickets_command_rejects_invalid_filter_value(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    db_path = tmp_path / "desk.db"

    with pytest.raises(SystemExit) as exc_info:
        main(["--db-path", str(db_path), "list-tickets", "--status", "done"])

    assert exc_info.value.code == 2
    error_output = capsys.readouterr().err
    assert error_output.startswith("Error: ")
