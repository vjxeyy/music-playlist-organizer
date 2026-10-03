# Music / Playlist Organiser

A menu-driven Python + MySQL program for managing songs and playlists
(Class 12 Computer Science project).

## Abstract

The project “Music / Playlist Organiser” is a database application developed
using Python as the front-end programming language and MySQL as the back-end
database. In today’s world, music plays an important role in entertainment
and relaxation, and people often have a large digital music collection.
Managing these songs manually becomes difficult, especially when it comes to
searching for tracks, categorising them, or creating playlists. This project
addresses that problem by providing an efficient way to organise songs and
playlists through a computerised system.

The system provides a menu-driven interface that allows the user to:

- Add new songs with details like title, artist, album, genre, and duration.
- View all songs stored in the database in a tabular format.
- Search songs by title, artist, or genre.
- Update song details if changes are needed.
- Delete songs that are no longer required.
- Create playlists and add songs to them.
- View all songs belonging to a specific playlist.

The Python program is used to take input from the user, display outputs, and
connect to the database using the mysql.connector library. The MySQL database
is used to store, update, and retrieve records, ensuring structured data
management. The project demonstrates how to perform CRUD operations (Create,
Read, Update, Delete), use foreign keys for linking tables (songs and
playlists), and manage relationships between data.

The objective of this project is not only to build a useful application but
also to give students practical exposure to the real-life use of Python with
SQL databases. By implementing this project, students learn about database
connectivity, SQL query execution, error handling, and modular programming in
Python. The project also simulates how popular music applications such as
Spotify, iTunes, or Wynk manage their backend operations.

In conclusion, the Music / Playlist Organiser project combines simplicity with
functionality, providing an easy-to-use platform to manage a music collection.
It highlights the importance of database applications in solving real-world
problems and demonstrates how Python and SQL can be integrated to create
efficient software solutions.

## Files

| File | Purpose |
|------|---------|
| `music_organiser.py` | Main program: run this |
| `db_config.example.py` | Template for `db_config.py` (MySQL username and password) |
| `setup_database.py` | Creates or resets `music_db` from `music_db.sql` |
| `music_db.sql` | Tables plus sample data (30 songs, 6 playlists) |
| `sample_queries.sql` | The 12 example queries from the report |
| `requirements.txt` | Python libraries needed |

## How to run

1. **Install and start MySQL Server** (8.0 or later).
   Download the Community Server from https://dev.mysql.com/downloads/mysql/.
2. **Install the Python libraries:**
   ```
   pip install -r requirements.txt
   ```
3. **Set your MySQL password:** copy `db_config.example.py` to
   `db_config.py` and change the password in the copy.
   `db_config.py` is in `.gitignore`, so your password is never committed.
   ```
   copy db_config.example.py db_config.py
   ```
4. **Run the program:**
   ```
   python music_organiser.py
   ```
   On the first run it offers to create `music_db` with the sample data.
   You can also create it by running `music_db.sql` in MySQL Workbench.

To restore the sample data later (for example before taking output
screenshots), run `python setup_database.py`. This deletes all changes.

## Menu

```
====== MUSIC / PLAYLIST ORGANISER ======
1. Add Song
2. View Songs
3. Search Song
4. Update Song
5. Delete Song
6. Create Playlist
7. Add Song to Playlist
8. View Playlist
9. Exit
```

## Changes from the source code in the report

The program keeps the report's structure (same tables, functions and menu)
but fixes these problems:

**Database (`music_db.sql`)**
- `PlaylistSongs` foreign keys now use `ON DELETE CASCADE`. Without it,
  **Delete Song failed with MySQL error 1451 for every sample song**,
  because all 30 are in a playlist.
- `PlaylistSongs` has a primary key `(playlist_id, song_id)`, so a song
  cannot be added to the same playlist twice.
- Playlist names are `UNIQUE`.
- The script starts with `DROP DATABASE IF EXISTS`, so it can be run again,
  and uses `utf8mb4` so titles like *Don’t Start Now* are stored correctly.
- The example queries are in their own file, `sample_queries.sql`.

**Python (`music_organiser.py`)**
- `tabulate` is listed as a requirement; the report's code imports it but
  only lists `mysql-connector-python`.
- The MySQL password is set in one place, `db_config.py`.
- A wrong password or a stopped MySQL server shows a clear message
  instead of a crash.
- **Update Song** edits every field (press Enter to keep a value). The
  report's version only changed title and artist, and said "updated
  successfully" even for a Song ID that does not exist.
- **Delete Song** shows the song and asks for confirmation first.
- **Add Song to Playlist** and **View Playlist** list the playlists before
  asking for an ID. A wrong ID or a duplicate now gives a message; in the
  report's version it crashed the program.
- Input is checked: title and artist are required, text must fit its
  column, and duration must look like `3:45`.
- **Add Song** warns when the same title and artist are already stored
  and asks before adding a copy.
- **Search Song** treats `%` and `_` as ordinary characters; in the
  report's version, searching `%` listed every song.
- Yes/no questions accept `y` or `yes`.
- **View Playlist** also shows the number of songs and the total time.

**Setup (`setup_database.py`)**
- Refuses to run if `music_db.sql` creates a different database from
  `DB_NAME` in `db_config.py`, instead of silently dropping it.
- Works even if `music_db.sql` was saved with a UTF-8 byte-order mark.
- If a table goes missing, the error message says how to rebuild it.

## Known limitation

`duration` is stored as text (`'3:20'`), as in the report. Sample queries
8, 9 and 11 compare it as text. That works while every song is under
10 minutes, because `'10:00'` sorts before `'9:59'`. Storing the duration in
seconds as an `INT` would remove this limit.
