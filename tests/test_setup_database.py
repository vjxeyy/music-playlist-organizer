"""setup_database.py: creating and resetting the database."""
import pytest

import setup_database as sd

pytestmark = pytest.mark.db


def counts(q):
    return q("SELECT (SELECT COUNT(*) FROM Songs), (SELECT COUNT(*) FROM Playlists), "
             "(SELECT COUNT(*) FROM PlaylistSongs)")[0]


def test_create_database_loads_the_sample_data(no_db, q):
    sd.create_database()
    assert counts(q) == (30, 6, 30)
    assert q("SELECT title, artist, duration FROM Songs WHERE song_id = 1") == [
        ("Blinding Lights", "The Weeknd", "3:20")]
    assert q("SELECT title FROM Songs WHERE song_id = 20") == [("Don’t Start Now",)]   # curly apostrophe


def test_create_database_resets_changes(fresh_db, q):
    q("DELETE FROM PlaylistSongs")
    q("DELETE FROM Songs")
    sd.create_database()
    assert counts(q) == (30, 6, 30)


def test_create_database_refuses_a_script_for_another_database(fresh_db, q, make_sql_file, monkeypatch):
    monkeypatch.setattr(sd, "SQL_FILE", make_sql_file("music_db_other"))
    with pytest.raises(RuntimeError, match="does not create 'music_db_test'"):
        sd.create_database()
    assert counts(q) == (30, 6, 30)          # nothing was dropped


def test_create_database_works_with_a_byte_order_mark(no_db, q, make_sql_file, monkeypatch):
    monkeypatch.setattr(sd, "SQL_FILE", make_sql_file("music_db_test", encoding="utf-8-sig"))
    sd.create_database()
    assert counts(q) == (30, 6, 30)


def test_database_exists(no_db):
    assert sd.database_exists() is False
    sd.create_database()
    assert sd.database_exists() is True


def test_main_creates_the_database_when_missing(no_db, run, q):
    out = run(sd.main, [])
    assert "is ready" in out
    assert counts(q) == (30, 6, 30)


@pytest.mark.parametrize("answer", ["n", "", "maybe"])
def test_main_reset_declined_changes_nothing(fresh_db, run, q, answer):
    q("DELETE FROM PlaylistSongs WHERE song_id = 1")
    out = run(sd.main, [answer])
    assert "Nothing changed." in out
    assert counts(q) == (30, 6, 29)


@pytest.mark.parametrize("answer", ["y", "yes"])
def test_main_reset_accepted_restores_sample_data(fresh_db, run, q, answer):
    q("DELETE FROM PlaylistSongs WHERE song_id = 1")
    out = run(sd.main, [answer])
    assert "is ready" in out
    assert counts(q) == (30, 6, 30)


def test_main_wrong_password_shows_guidance(run, monkeypatch):
    monkeypatch.setitem(sd.DB_CONFIG, "password", "definitely-wrong-password")
    out = run(sd.main, [])
    assert "rejected the username/password" in out
