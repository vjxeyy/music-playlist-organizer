"""Input checks and helper functions. No database needed."""
import mysql.connector
import pytest
from mysql.connector import errorcode

import music_organiser as mo
import setup_database as sd


def ask(run, func, answers):
    """Run a one-question helper; return (its result, what it printed)."""
    result = []
    out = run(lambda: result.append(func()), answers)
    return result[0], out


# ---------------------------------------------------------------- read_text
def test_read_text_required_re_asks_until_not_blank(run):
    value, out = ask(run, lambda: mo.read_text("Title: ", 100, required=True), ["", "   ", "Hello"])
    assert value == "Hello"
    assert out.count("This field cannot be empty.") == 2


def test_read_text_optional_blank_gives_none(run):
    value, _ = ask(run, lambda: mo.read_text("Album: ", 100), [""])
    assert value is None


def test_read_text_trims_spaces(run):
    value, _ = ask(run, lambda: mo.read_text("Title: ", 100), ["  Spaced Out  "])
    assert value == "Spaced Out"


def test_read_text_length_limit(run):
    value, out = ask(run, lambda: mo.read_text("Genre: ", 50), ["G" * 51, "G" * 50])
    assert value == "G" * 50
    assert "within 50 characters" in out


# ---------------------------------------------------------------- read_duration
@pytest.mark.parametrize("typed, stored", [
    ("3:45", "3:45"), ("03:45", "3:45"), (" 12:05 ", "12:05"), ("0:01", "0:01"), ("999:59", "999:59"),
])
def test_read_duration_valid(run, typed, stored):
    value, _ = ask(run, lambda: mo.read_duration("Duration: "), [typed])
    assert value == stored


@pytest.mark.parametrize("bad", [
    "3:60", "3:5", "3", ":45", "3:45:00", "-3:45", "3.45", "0:00", "1000:00", "३:४५", "abc", "3 :45",
])
def test_read_duration_rejects_and_re_asks(run, bad):
    value, out = ask(run, lambda: mo.read_duration("Duration: "), [bad, "1:00"])
    assert value == "1:00"
    assert out.count("Please use the format mm:ss") == 1


def test_read_duration_blank_gives_none(run):
    value, _ = ask(run, lambda: mo.read_duration("Duration: "), [""])
    assert value is None


# ---------------------------------------------------------------- read_id
@pytest.mark.parametrize("typed, expected", [("7", 7), (" 12 ", 12)])
def test_read_id_valid(run, typed, expected):
    value, _ = ask(run, lambda: mo.read_id("ID: "), [typed])
    assert value == expected


@pytest.mark.parametrize("bad", ["abc", "0", "-5", "1.5", ""])
def test_read_id_invalid(run, bad):
    value, out = ask(run, lambda: mo.read_id("ID: "), [bad])
    assert value is None
    assert "Please enter a valid ID number." in out


# ---------------------------------------------------------------- small helpers
@pytest.mark.parametrize("text, pattern", [
    ("rock", "%rock%"), ("100%", "%100!%%"), ("a_b", "%a!_b%"), ("hi!", "%hi!!%"),
])
def test_like_pattern_escapes_wildcards(text, pattern):
    assert mo.like_pattern(text) == pattern


def row(duration):
    return (1, "t", "a", None, None, duration)


def test_total_duration_adds_minutes_and_seconds():
    assert mo.total_duration([row("3:20"), row("4:55")]) == "8:15"


def test_total_duration_skips_blank_and_badly_formatted_values():
    rows = [row("3.20"), row("abc"), row(""), row(None), row("10:05"), row("1:2:3")]
    assert mo.total_duration(rows) == "10:05"


def test_total_duration_over_an_hour():
    assert mo.total_duration([row("25:10")] * 3) == "75:30"


@pytest.mark.parametrize("answer, expected", [
    ("y", True), ("Y", True), ("yes", True), (" YES ", True),
    ("n", False), ("no", False), ("", False), ("maybe", False), ("nope", False),
])
def test_is_yes(answer, expected):
    assert sd.is_yes(answer) is expected


# ---------------------------------------------------------------- setup_database helpers
def test_read_statements_splits_music_db_sql(test_sql_file):
    statements = sd.read_statements(test_sql_file)
    assert len(statements) == 9
    assert statements[0] == "DROP DATABASE IF EXISTS music_db_test"
    assert statements[-1].startswith("INSERT INTO PlaylistSongs")


def test_read_statements_accepts_a_byte_order_mark(make_sql_file):
    path = make_sql_file("music_db_test", encoding="utf-8-sig")
    assert sd.read_statements(path)[0] == "DROP DATABASE IF EXISTS music_db_test"


@pytest.mark.parametrize("errno, text", [
    (errorcode.ER_ACCESS_DENIED_ERROR, "rejected the username/password"),
    (errorcode.CR_CONN_HOST_ERROR, "Make sure MySQL Server is installed and running"),
    (errorcode.CR_CONNECTION_ERROR, "Make sure MySQL Server is installed and running"),
    (errorcode.ER_NO_SUCH_TABLE, "setup_database.py"),
    (1064, "MySQL error 1064"),
])
def test_describe_error(errno, text):
    assert text in sd.describe_error(mysql.connector.Error(msg="details", errno=errno))


def test_describe_error_non_mysql_error():
    assert sd.describe_error(RuntimeError("plain message")) == "plain message"
