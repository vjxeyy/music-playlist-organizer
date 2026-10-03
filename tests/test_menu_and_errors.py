"""The main menu, starting the program, connection problems, and the sample queries."""
import os

import mysql.connector
import pytest

import music_organiser as mo
import setup_database as sd

pytestmark = pytest.mark.db
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

GOODBYE = "Exiting program. Goodbye!"
SERVER_DOWN = "Make sure MySQL Server is installed and running"


# ---------------------------------------------------------------- safety guard
def test_guard_blocks_the_real_database(real_db_error):
    with pytest.raises(real_db_error):
        mysql.connector.connect(**mo.DB_CONFIG, database="music_db")
    conn = mysql.connector.connect(**mo.DB_CONFIG)
    try:
        with pytest.raises(real_db_error):
            conn.cursor().execute("SELECT COUNT(*) FROM music_db.Songs")   # harmless if it got through
    finally:
        conn.close()


# ---------------------------------------------------------------- main menu
@pytest.mark.usefixtures("fresh_db")
def test_menu_rejects_invalid_choices(run):
    out = run(mo.main_menu, ["0", "10", "abc", "", "-1", "2.0", "   ", "9"])
    assert out.count("Invalid choice, please try again.") == 7
    assert GOODBYE in out


@pytest.mark.usefixtures("fresh_db")
def test_menu_accepts_a_choice_with_spaces(run):
    assert "🎶 All Songs:" in run(mo.main_menu, [" 2 ", "9"])


# ---------------------------------------------------------------- starting the program
@pytest.mark.parametrize("answer", ["y", "Y", "yes"])
def test_first_run_creates_the_database(no_db, run, q, answer):
    out = run(mo.main, [answer, "9"])
    assert "does not exist yet" in out and "'music_db_test' created" in out
    assert "MUSIC / PLAYLIST ORGANISER" in out
    assert q("SELECT COUNT(*) FROM Songs") == [(30,)]


@pytest.mark.parametrize("answer", ["n", "", "maybe"])
def test_first_run_declined(no_db, run, answer):
    out = run(mo.main, [answer])
    assert "python setup_database.py" in out
    assert "MUSIC / PLAYLIST ORGANISER" not in out
    assert sd.database_exists() is False


def test_wrong_password(run, monkeypatch):
    monkeypatch.setitem(mo.DB_CONFIG, "password", "definitely-wrong-password")
    out = run(mo.main, [])
    assert "rejected the username/password" in out
    assert "MUSIC / PLAYLIST ORGANISER" not in out


def test_server_not_reachable(run, monkeypatch):
    monkeypatch.setitem(mo.DB_CONFIG, "port", 1)
    assert SERVER_DOWN in run(mo.main, [])


@pytest.mark.usefixtures("fresh_db")
def test_server_stops_mid_session(run, monkeypatch):
    monkeypatch.setitem(mo.DB_CONFIG, "port", 1)       # every action now fails to connect
    out = run(mo.main_menu, ["2", "3", "Coldplay", "6", "X", "8", "9"])
    assert out.count(SERVER_DOWN) == 4
    assert GOODBYE in out


@pytest.mark.usefixtures("fresh_db")
def test_ctrl_c_at_the_menu(run):
    assert GOODBYE in run(mo.main, [KeyboardInterrupt])


@pytest.mark.usefixtures("fresh_db")
def test_ctrl_c_while_adding_saves_nothing(run, song_id):
    out = run(mo.main, ["1", "Half a song", KeyboardInterrupt])
    assert GOODBYE in out
    assert song_id("Half a song") is None


@pytest.mark.usefixtures("fresh_db")
def test_input_closed_at_the_menu(run):
    assert GOODBYE in run(mo.main, [])


@pytest.mark.usefixtures("fresh_db")
def test_input_closed_while_updating_changes_nothing(run, q):
    out = run(mo.main, ["4", "1", "New title"])
    assert GOODBYE in out
    assert q("SELECT title FROM Songs WHERE song_id = 1") == [("Blinding Lights",)]


@pytest.mark.usefixtures("fresh_db")
def test_missing_table_points_to_setup_script(run, q):
    q("DROP TABLE PlaylistSongs")
    out = run(mo.main_menu, ["8", "2", "9"])
    assert "setup_database.py" in out            # option 8 explains how to fix it
    assert "🎶 All Songs:" in out                 # other options still work


# ---------------------------------------------------------------- sample_queries.sql
@pytest.mark.usefixtures("fresh_db")
def test_sample_queries_run_on_the_sample_data(q):
    statements = [s for s in sd.read_statements(os.path.join(PROJECT_DIR, "sample_queries.sql"))
                  if not s.upper().startswith("USE ")]
    assert len(statements) == 12
    results = [q(s) for s in statements]
    assert len(results[0]) == 30                                                  # 1. all songs
    assert [r[1] for r in results[1]][:2] == ["My Favorites", "Workout Vibes"]   # 2. in ID order
    assert {r[0] for r in results[2]} == {"Paradise", "Believer", "Thunder", "Levitating", "Sorry"}
    assert results[7] == [("Fix You", "Coldplay", "4:55")]                       # 8. longest song
    assert results[11] == [(30,)]                                                # 12. total songs
