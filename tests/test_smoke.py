from pathlib import Path

from desktickets_v2.main import main


def test_create_ticket_command_persists_ticket(tmp_path: Path, capsys) -> None:
    db_path = tmp_path / "desktickets.db"

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
    assert capsys.readouterr().out.strip() == "OK: ticket created (id=1)"
