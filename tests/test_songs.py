"""Menu options 1-5: add, view, search, update and delete songs."""
import pytest

import music_organiser as mo

pytestmark = [pytest.mark.db, pytest.mark.usefixtures("fresh_db")]

SONG = "SELECT title, artist, album, genre, duration FROM Songs WHERE song_id = %s"


# ---------------------------------------------------------------- 1. Add Song
def test_add_song_stores_every_field(run, q):
    out = run(mo.add_song, ["Test Song", "Tester", "Test Album", "Pop", "3:45"])
    assert "Song added successfully! (Song ID: 31)" in out
    assert q(SONG, 31) == [("Test Song", "Tester", "Test Album", "Pop", "3:45")]


def test_add_song_blank_optional_fields_are_null(run, q):
    run(mo.add_song, ["Bare", "Someone", "", "", ""])
    assert q(SONG, 31) == [("Bare", "Someone", None, None, None)]


def test_add_song_re_asks_for_title_and_artist(run, song_id):
    out = run(mo.add_song, ["   ", "T" * 101, "Real Title", "", "Real Artist", "", "", ""])
    assert out.count("This field cannot be empty.") == 2
    assert "within 100 characters" in out
    assert song_id("Real Title") == 31


def test_add_song_accepts_exactly_100_characters(run, song_id):
    run(mo.add_song, ["T" * 100, "A", "", "", ""])
    assert song_id("T" * 100) == 31


def test_add_song_re_asks_for_a_bad_duration(run, q):
    out = run(mo.add_song, ["Dur", "A", "", "", "3.45", "3:60", "03:45"])
    assert out.count("Please use the format mm:ss") == 2
    assert q("SELECT duration FROM Songs WHERE song_id = 31") == [("3:45",)]


def test_add_song_trims_spaces(run, q):
    run(mo.add_song, ["  Spaced Out  ", "  Trim Me  ", "", "", ""])
    assert q("SELECT title, artist FROM Songs WHERE song_id = 31") == [("Spaced Out", "Trim Me")]


def test_add_song_emoji_and_accented_text_round_trip(run, q):
    title = "🔥" * 100
    run(mo.add_song, [title, "Señor Ñandú – 世界", "", "", ""])
    assert q("SELECT title, artist FROM Songs WHERE song_id = 31") == [(title, "Señor Ñandú – 世界")]


@pytest.mark.parametrize("title", ["Robert'); DROP TABLE Songs;--", "100% Pure_Love"])
def test_add_song_stores_special_characters_literally(run, q, song_id, title):
    run(mo.add_song, [title, "Tester", "", "", ""])
    assert song_id(title) == 31
    assert q("SELECT COUNT(*) FROM Songs") == [(31,)]


def test_add_song_duplicate_warns_and_n_skips(run, q):
    out = run(mo.add_song, ["believer", "IMAGINE DRAGONS", "n"])
    assert "already in the database (Song ID: 12)" in out
    assert "Song not added." in out
    assert q("SELECT COUNT(*) FROM Songs") == [(30,)]


def test_add_song_duplicate_yes_adds_anyway(run, q):
    run(mo.add_song, ["Believer", "Imagine Dragons", "yes", "Evolve", "Rock", "3:24"])
    assert q("SELECT COUNT(*) FROM Songs WHERE title = 'Believer'") == [(2,)]


# ---------------------------------------------------------------- 2. View Songs
def test_view_songs_lists_everything(run):
    out = run(mo.view_songs, [])
    assert "🎶 All Songs:" in out
    assert "Blinding Lights" in out and "We Don’t Talk Anymore" in out
    assert "Total songs: 30" in out


def test_view_songs_shows_null_fields_as_blank(run):
    run(mo.add_song, ["No Details", "Someone", "", "", ""])
    assert "None" not in run(mo.view_songs, [])


def test_view_songs_empty_table(run, q):
    q("DELETE FROM PlaylistSongs")
    q("DELETE FROM Songs")
    assert "No songs yet" in run(mo.view_songs, [])


# ---------------------------------------------------------------- 3. Search Song
@pytest.mark.parametrize("keyword, expected", [
    ("WEEKND", ["Blinding Lights", "Save Your Tears", "Starboy"]),          # artist, any case
    ("dragons", ["Believer", "Thunder", "Radioactive", "Demons"]),          # part of an artist
    ("alternative", ["Viva La Vida", "Radioactive", "Demons"]),             # genre
    ("señorita", ["Senorita"]),                                             # accents ignored
])
def test_search_finds_matches(run, keyword, expected):
    out = run(mo.search_song, [keyword])
    assert f"Search Results for '{keyword}'" in out
    for title in expected:
        assert title in out


@pytest.mark.parametrize("keyword", ["zzzz", "' OR '1'='1"])
def test_search_no_match(run, keyword):
    assert f"No songs match '{keyword}'" in run(mo.search_song, [keyword])


@pytest.mark.parametrize("keyword", ["%", "_"])
def test_search_wildcards_are_literal(run, keyword):
    run(mo.add_song, ["100% Pure_Love", "Wildcard", "", "", ""])
    out = run(mo.search_song, [keyword])
    assert "100% Pure_Love" in out
    assert "Blinding Lights" not in out


def test_search_re_asks_for_a_keyword(run):
    out = run(mo.search_song, ["", "k" * 101, "Coldplay"])
    assert "This field cannot be empty." in out
    assert "within 100 characters" in out
    assert "Fix You" in out


# ---------------------------------------------------------------- 4. Update Song
@pytest.mark.parametrize("bad", ["abc", "0", "-5", "1.5", ""])
def test_update_rejects_a_bad_id(run, bad):
    assert "Please enter a valid ID number." in run(mo.update_song, [bad])


@pytest.mark.parametrize("missing", ["9999", "99999999999999999999"])
def test_update_missing_song(run, missing):
    assert "Song not found!" in run(mo.update_song, [missing])


def test_update_blank_answers_keep_everything(run, q):
    before = q(SONG, 5)
    out = run(mo.update_song, ["5", "", "", "", "", ""])
    assert "Current details:" in out and "New Title [Hymn for the Weekend]" in out
    assert q(SONG, 5) == before


def test_update_one_field(run, q):
    run(mo.update_song, ["6", "", "", "", "Indie", ""])
    assert q(SONG, 6) == [("Viva La Vida", "Coldplay", "Viva La Vida", "Indie", "4:02")]


def test_update_re_asks_for_bad_values(run, q):
    out = run(mo.update_song, ["8", "S" * 101, "Shape Of You (Remix)", "", "", "", "4.55", "5:01"])
    assert "within 100 characters" in out and "Please use the format" in out
    assert q(SONG, 8) == [("Shape Of You (Remix)", "Ed Sheeran", "Divide", "Pop", "5:01")]


def test_update_song_with_empty_fields(run, q):
    run(mo.add_song, ["Bare", "Someone", "", "", ""])
    out = run(mo.update_song, ["31", "", "", "New Album", "", "2:00"])
    assert "New Album []" in out
    assert q(SONG, 31) == [("Bare", "Someone", "New Album", None, "2:00")]


# ---------------------------------------------------------------- 5. Delete Song
def test_delete_bad_and_missing_ids(run):
    assert "Please enter a valid ID number." in run(mo.delete_song, ["x"])
    assert "Song not found!" in run(mo.delete_song, ["9999"])


@pytest.mark.parametrize("answer", ["n", "", "no", "nope"])
def test_delete_cancelled(run, song_id, answer):
    out = run(mo.delete_song, ["1", answer])
    assert "Delete cancelled." in out
    assert song_id("Blinding Lights") == 1


@pytest.mark.parametrize("answer", ["y", "Y", "yes"])
def test_delete_confirmed(run, song_id, answer):
    out = run(mo.delete_song, ["1", answer])
    assert "'Blinding Lights' deleted successfully!" in out
    assert song_id("Blinding Lights") is None


def test_delete_removes_the_song_from_every_playlist(run, q):
    q("INSERT INTO PlaylistSongs (playlist_id, song_id) VALUES (3, 12)")   # Believer now in 2 playlists
    out = run(mo.delete_song, ["12", "y"])
    assert "removed from 2 playlist(s)" in out
    assert q("SELECT COUNT(*) FROM PlaylistSongs WHERE song_id = 12") == [(0,)]


def test_delete_song_in_no_playlist_has_no_playlist_warning(run, song_id):
    run(mo.add_song, ["Loner", "Solo", "", "", ""])
    out = run(mo.delete_song, ["31", "y"])
    assert "removed from" not in out
    assert song_id("Loner") is None
