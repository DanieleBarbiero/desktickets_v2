from desktickets_v2.main import greet


def test_greet_returns_expected_text():
    assert greet() == "hello from desktickets_v2"