"""Menu options 6-8: create playlists, add songs to them, and view them."""
import pytest

import music_organiser as mo

pytestmark = [pytest.mark.db, pytest.mark.usefixtures("fresh_db")]


@pytest.fixture
def gym(q):
    """An empty playlist called Gym; returns its ID."""
    return q("INSERT INTO Playlists (playlist_name) VALUES ('Gym')")


# ---------------------------------------------------------------- 6. Create Playlist
def test_create_playlist(run, q):
    out = run(mo.create_playlist, ["Late Night Drive"])
    assert "Playlist 'Late Night Drive' created successfully! (Playlist ID: 7)" in out
    assert q("SELECT playlist_name FROM Playlists WHERE playlist_id = 7") == [("Late Night Drive",)]


@pytest.mark.parametrize("name", ["Gym", "GYM", "  Gym  "])
def test_create_playlist_refuses_duplicates(run, q, gym, name):
    out = run(mo.create_playlist, [name])
    assert "already exists" in out
    assert q("SELECT COUNT(*) FROM Playlists WHERE playlist_name = 'Gym'") == [(1,)]


def test_create_playlist_re_asks_for_a_name(run, q):
    out = run(mo.create_playlist, ["", "P" * 101, "P" * 100])
    assert "This field cannot be empty." in out and "within 100 characters" in out
    assert q("SELECT COUNT(*) FROM Playlists WHERE playlist_name = %s", "P" * 100) == [(1,)]


def test_create_playlist_stores_special_characters_literally(run, q):
    name = "x'); DELETE FROM Playlists;--"
    run(mo.create_playlist, [name])
    assert q("SELECT COUNT(*) FROM Playlists") == [(7,)]
    assert q("SELECT COUNT(*) FROM Playlists WHERE playlist_name = %s", name) == [(1,)]


# ---------------------------------------------------------------- 7. Add Song to Playlist
def test_add_song_to_playlist(run, q, gym):
    out = run(mo.add_song_to_playlist, [str(gym), "13"])
    assert "📂 Playlists:" in out and "Road Trip" in out          # playlists are listed first
    assert "'Thunder' added to 'Gym' successfully!" in out
    assert q("SELECT song_id FROM PlaylistSongs WHERE playlist_id = %s", gym) == [(13,)]


def test_add_song_to_playlist_refuses_a_duplicate(run, gym):
    run(mo.add_song_to_playlist, [str(gym), "13"])
    assert "'Thunder' is already in 'Gym'." in run(mo.add_song_to_playlist, [str(gym), "13"])


@pytest.mark.parametrize("answers, message", [
    (["x"], "Please enter a valid ID number."),
    (["9999"], "Playlist not found!"),
    (["1", "x"], "Please enter a valid ID number."),
    (["1", "9999"], "Song not found!"),
])
def test_add_song_to_playlist_bad_ids(run, answers, message):
    assert message in run(mo.add_song_to_playlist, answers)


# ---------------------------------------------------------------- 8. View Playlist
def test_view_playlist_shows_songs_and_total_time(run):
    out = run(mo.view_playlist, ["2"])
    assert "📂 Playlist: Workout Vibes" in out
    assert "5 song(s), total time 17:26" in out          # 4:12 + 3:24 + 3:07 + 3:23 + 3:20


def test_view_empty_playlist(run, gym):
    assert "Playlist 'Gym' is empty" in run(mo.view_playlist, [str(gym)])


@pytest.mark.parametrize("answer, message", [
    ("9999", "Playlist not found!"), ("x", "Please enter a valid ID number."),
])
def test_view_playlist_bad_ids(run, answer, message):
    assert message in run(mo.view_playlist, [answer])


def test_view_playlist_ignores_badly_formatted_durations(run, q, gym):
    # Durations typed straight into MySQL (e.g. in Workbench) that the program would never store.
    for title, duration in (("W1", "3.20"), ("W2", "abc"), ("W3", ""), ("W4", None), ("W5", "10:05")):
        new_id = q("INSERT INTO Songs (title, artist, duration) VALUES (%s, 'X', %s)", title, duration)
        q("INSERT INTO PlaylistSongs VALUES (%s, %s)", gym, new_id)
    assert "5 song(s), total time 10:05" in run(mo.view_playlist, [str(gym)])


def test_view_playlist_total_over_an_hour(run, q, gym):
    for title in ("L1", "L2", "L3"):
        new_id = q("INSERT INTO Songs (title, artist, duration) VALUES (%s, 'X', '25:10')", title)
        q("INSERT INTO PlaylistSongs VALUES (%s, %s)", gym, new_id)
    assert "3 song(s), total time 75:30" in run(mo.view_playlist, [str(gym)])


@pytest.mark.parametrize("func", [mo.add_song_to_playlist, mo.view_playlist])
def test_no_playlists_yet(run, q, func):
    q("DELETE FROM PlaylistSongs")
    q("DELETE FROM Playlists")
    assert "No playlists yet" in run(func, [])
