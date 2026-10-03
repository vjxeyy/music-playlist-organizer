# ---------------------------------------------------
# Project: Music / Playlist Organiser
# Language: Python 3.x
# Database: MySQL (music_db)
# Libraries Required: mysql-connector-python, tabulate
# Run: python music_organiser.py
# ---------------------------------------------------

import re
import sys

import mysql.connector
from mysql.connector import errorcode
from tabulate import tabulate

try:
    from db_config import DB_CONFIG, DB_NAME
except ModuleNotFoundError:
    sys.exit("db_config.py not found. Copy db_config.example.py to db_config.py "
             "and put your MySQL password in it.")
from setup_database import create_database, describe_error, is_yes

SONG_HEADERS = ["ID", "Title", "Artist", "Album", "Genre", "Duration"]


# ---------------------------------------------------
# Database Connection
# ---------------------------------------------------
def connect_db():
    # buffered=True makes each cursor fetch its whole result straight away,
    # so one cursor can run several queries in a row.
    return mysql.connector.connect(**DB_CONFIG, database=DB_NAME, buffered=True)


def check_database():
    """Make sure MySQL is reachable and music_db exists before showing the menu."""
    try:
        connect_db().close()
        return True
    except mysql.connector.Error as err:
        if err.errno != errorcode.ER_BAD_DB_ERROR:
            print("\n❌ " + describe_error(err) + "\n")
            return False

    print(f"\nThe database '{DB_NAME}' does not exist yet.")
    answer = input("Create it now with the sample songs and playlists? (y/n): ")
    if not is_yes(answer):
        print("You can create it later with: python setup_database.py")
        return False
    try:
        create_database()
    except (mysql.connector.Error, RuntimeError) as err:
        print("\n❌ " + describe_error(err) + "\n")
        return False
    print(f"✅ '{DB_NAME}' created.\n")
    return True


# ---------------------------------------------------
# Input and Display Helpers
# ---------------------------------------------------
def read_text(prompt, max_len, required=False):
    """Ask until the answer fits the column. A blank optional answer gives None."""
    while True:
        value = input(prompt).strip()
        if not value and required:
            print("   This field cannot be empty.")
        elif len(value) > max_len:
            print(f"   Please keep it within {max_len} characters.")
        else:
            return value or None


def read_duration(prompt):
    """Ask for a duration like 3:45 and return it as 'm:ss' (None if left blank)."""
    while True:
        value = input(prompt).strip()
        if not value:
            return None
        match = re.fullmatch(r"(\d{1,3}):([0-5]\d)", value, re.ASCII)
        if match:
            minutes, seconds = int(match.group(1)), match.group(2)
            if minutes or seconds != "00":
                return f"{minutes}:{seconds}"
        print("   Please use the format mm:ss, e.g. 3:45")


def read_id(prompt):
    """Return the ID typed, or None (after a message) if it is not a positive number."""
    value = input(prompt).strip()
    try:
        number = int(value)
    except ValueError:
        number = 0
    if number > 0:
        return number
    print("\n❌ Please enter a valid ID number.\n")
    return None


def like_pattern(text):
    """LIKE pattern that finds text anywhere, treating % and _ as ordinary
    characters (used with ESCAPE '!')."""
    escaped = text.replace("!", "!!").replace("%", "!%").replace("_", "!_")
    return "%" + escaped + "%"


def print_songs(heading, rows):
    print(f"\n{heading}\n")
    print(tabulate(rows, headers=SONG_HEADERS, tablefmt="grid", disable_numparse=True))


def total_duration(rows):
    """Add up the 'm:ss' durations in the last column, skipping blank or odd values."""
    seconds = 0
    for row in rows:
        try:
            minutes, secs = row[5].split(":")
            seconds += int(minutes) * 60 + int(secs)
        except (AttributeError, ValueError):
            pass
    return f"{seconds // 60}:{seconds % 60:02d}"


def fetch_song(cur, song_id):
    cur.execute("SELECT song_id, title, artist, album, genre, duration "
                "FROM Songs WHERE song_id = %s", (song_id,))
    return cur.fetchone()


def fetch_playlist_name(cur, playlist_id):
    cur.execute("SELECT playlist_name FROM Playlists WHERE playlist_id = %s",
                (playlist_id,))
    row = cur.fetchone()
    return row[0] if row else None


def show_playlists(cur):
    """Print every playlist with its song count. Returns False if there are none."""
    cur.execute("SELECT p.playlist_id, p.playlist_name, COUNT(ps.song_id) "
                "FROM Playlists p LEFT JOIN PlaylistSongs ps "
                "ON p.playlist_id = ps.playlist_id "
                "GROUP BY p.playlist_id, p.playlist_name "
                "ORDER BY p.playlist_id")
    rows = cur.fetchall()
    if not rows:
        print("\nNo playlists yet. Use option 6 to create one.\n")
        return False
    print("\n📂 Playlists:\n")
    print(tabulate(rows, headers=["ID", "Playlist", "Songs"], tablefmt="grid",
                   disable_numparse=True))
    return True


# ---------------------------------------------------
# Song Module
# ---------------------------------------------------
def add_song():
    title = read_text("Enter Song Title: ", 100, required=True)
    artist = read_text("Enter Artist: ", 100, required=True)

    db = connect_db()
    try:
        cur = db.cursor()
        # Same title and artist (ignoring case) already stored? Ask before adding a copy.
        cur.execute("SELECT song_id FROM Songs WHERE title = %s AND artist = %s",
                    (title, artist))
        existing = cur.fetchone()
        if existing:
            print(f"\n⚠️ '{title}' by {artist} is already in the database "
                  f"(Song ID: {existing[0]}).")
            if not is_yes(input("Add it again anyway? (y/n): ")):
                print("\nSong not added.\n")
                return

        album = read_text("Enter Album: ", 100)
        genre = read_text("Enter Genre: ", 50)
        duration = read_duration("Enter Duration (mm:ss): ")

        cur.execute("INSERT INTO Songs (title, artist, album, genre, duration) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    (title, artist, album, genre, duration))
        db.commit()
        print(f"\n✅ Song added successfully! (Song ID: {cur.lastrowid})\n")
    finally:
        db.close()


def view_songs():
    db = connect_db()
    try:
        cur = db.cursor()
        cur.execute("SELECT song_id, title, artist, album, genre, duration "
                    "FROM Songs ORDER BY song_id")
        rows = cur.fetchall()
    finally:
        db.close()

    if rows:
        print_songs("🎶 All Songs:", rows)
        print(f"Total songs: {len(rows)}\n")
    else:
        print("\nNo songs yet. Use option 1 to add one.\n")


def search_song():
    keyword = read_text("Enter keyword (title/artist/genre): ", 100, required=True)
    pattern = like_pattern(keyword)

    db = connect_db()
    try:
        cur = db.cursor()
        cur.execute("SELECT song_id, title, artist, album, genre, duration FROM Songs "
                    "WHERE title LIKE %s ESCAPE '!' OR artist LIKE %s ESCAPE '!' "
                    "OR genre LIKE %s ESCAPE '!' "
                    "ORDER BY song_id",
                    (pattern, pattern, pattern))
        rows = cur.fetchall()
    finally:
        db.close()

    if rows:
        print_songs(f"🔍 Search Results for '{keyword}':", rows)
    else:
        print(f"\nNo songs match '{keyword}'.\n")


# ---------------------------------------------------
# Update / Delete Module
# ---------------------------------------------------
def update_song():
    song_id = read_id("Enter Song ID to update: ")
    if song_id is None:
        return

    db = connect_db()
    try:
        cur = db.cursor()
        song = fetch_song(cur, song_id)
        if song is None:
            print("\n❌ Song not found!\n")
            return

        print_songs("Current details:", [song])
        print("Type a new value, or press Enter to keep the current one.\n")
        title = read_text(f"New Title [{song[1]}]: ", 100) or song[1]
        artist = read_text(f"New Artist [{song[2]}]: ", 100) or song[2]
        album = read_text(f"New Album [{song[3] or ''}]: ", 100) or song[3]
        genre = read_text(f"New Genre [{song[4] or ''}]: ", 50) or song[4]
        duration = read_duration(f"New Duration (mm:ss) [{song[5] or ''}]: ") or song[5]

        cur.execute("UPDATE Songs SET title=%s, artist=%s, album=%s, genre=%s, duration=%s "
                    "WHERE song_id=%s",
                    (title, artist, album, genre, duration, song_id))
        db.commit()
        print("\n✏️ Song updated successfully!\n")
    finally:
        db.close()


def delete_song():
    song_id = read_id("Enter Song ID to delete: ")
    if song_id is None:
        return

    db = connect_db()
    try:
        cur = db.cursor()
        song = fetch_song(cur, song_id)
        if song is None:
            print("\n❌ Song not found!\n")
            return

        cur.execute("SELECT COUNT(*) FROM PlaylistSongs WHERE song_id = %s", (song_id,))
        playlist_count = cur.fetchone()[0]
        print_songs("Song to delete:", [song])
        if playlist_count:
            print(f"It will also be removed from {playlist_count} playlist(s).")
        if not is_yes(input("Are you sure? (y/n): ")):
            print("\nDelete cancelled.\n")
            return

        # ON DELETE CASCADE in music_db.sql removes its PlaylistSongs rows too.
        cur.execute("DELETE FROM Songs WHERE song_id=%s", (song_id,))
        db.commit()
        print(f"\n🗑️ '{song[1]}' deleted successfully!\n")
    finally:
        db.close()


# ---------------------------------------------------
# Playlist Module
# ---------------------------------------------------
def create_playlist():
    playlist_name = read_text("Enter Playlist Name: ", 100, required=True)

    db = connect_db()
    try:
        cur = db.cursor()
        cur.execute("INSERT INTO Playlists (playlist_name) VALUES (%s)", (playlist_name,))
        db.commit()
        print(f"\n✅ Playlist '{playlist_name}' created successfully! "
              f"(Playlist ID: {cur.lastrowid})\n")
    except mysql.connector.IntegrityError as err:
        if err.errno != errorcode.ER_DUP_ENTRY:
            raise
        print(f"\n❌ A playlist named '{playlist_name}' already exists.\n")
    finally:
        db.close()


def add_song_to_playlist():
    db = connect_db()
    try:
        cur = db.cursor()
        if not show_playlists(cur):
            return
        playlist_id = read_id("Enter Playlist ID: ")
        if playlist_id is None:
            return
        playlist_name = fetch_playlist_name(cur, playlist_id)
        if playlist_name is None:
            print("\n❌ Playlist not found!\n")
            return

        song_id = read_id("Enter Song ID (options 2 and 3 show song IDs): ")
        if song_id is None:
            return
        song = fetch_song(cur, song_id)
        if song is None:
            print("\n❌ Song not found!\n")
            return

        try:
            cur.execute("INSERT INTO PlaylistSongs (playlist_id, song_id) VALUES (%s, %s)",
                        (playlist_id, song_id))
            db.commit()
        except mysql.connector.IntegrityError as err:
            if err.errno != errorcode.ER_DUP_ENTRY:
                raise
            print(f"\n'{song[1]}' is already in '{playlist_name}'.\n")
            return
        print(f"\n🎵 '{song[1]}' added to '{playlist_name}' successfully!\n")
    finally:
        db.close()


def view_playlist():
    db = connect_db()
    try:
        cur = db.cursor()
        if not show_playlists(cur):
            return
        playlist_id = read_id("Enter Playlist ID: ")
        if playlist_id is None:
            return
        playlist_name = fetch_playlist_name(cur, playlist_id)
        if playlist_name is None:
            print("\n❌ Playlist not found!\n")
            return

        cur.execute("""SELECT s.song_id, s.title, s.artist, s.album, s.genre, s.duration
                       FROM Songs s JOIN PlaylistSongs ps ON s.song_id = ps.song_id
                       WHERE ps.playlist_id = %s
                       ORDER BY s.song_id""", (playlist_id,))
        rows = cur.fetchall()
    finally:
        db.close()

    if rows:
        print_songs(f"📂 Playlist: {playlist_name}", rows)
        print(f"{len(rows)} song(s), total time {total_duration(rows)}\n")
    else:
        print(f"\n📂 Playlist '{playlist_name}' is empty. Use option 7 to add songs.\n")


# ---------------------------------------------------
# Main Menu
# ---------------------------------------------------
def main_menu():
    while True:
        print("\n====== MUSIC / PLAYLIST ORGANISER ======")
        print("1. Add Song")
        print("2. View Songs")
        print("3. Search Song")
        print("4. Update Song")
        print("5. Delete Song")
        print("6. Create Playlist")
        print("7. Add Song to Playlist")
        print("8. View Playlist")
        print("9. Exit")

        choice = input("Enter your choice: ").strip()

        # A database problem (e.g. MySQL stopped) shows a message instead of crashing.
        try:
            if choice == '1':
                add_song()
            elif choice == '2':
                view_songs()
            elif choice == '3':
                search_song()
            elif choice == '4':
                update_song()
            elif choice == '5':
                delete_song()
            elif choice == '6':
                create_playlist()
            elif choice == '7':
                add_song_to_playlist()
            elif choice == '8':
                view_playlist()
            elif choice == '9':
                print("\n👋 Exiting program. Goodbye!\n")
                break
            else:
                print("\n❌ Invalid choice, please try again.\n")
        except mysql.connector.Error as err:
            print("\n❌ " + describe_error(err) + "\n")


# ---------------------------------------------------
# Run Program
# ---------------------------------------------------
if __name__ == "__main__":
    # Lets emoji print safely on older Windows consoles and when output is redirected.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    try:
        if check_database():
            main_menu()
    except (KeyboardInterrupt, EOFError):
        print("\n\n👋 Exiting program. Goodbye!\n")
