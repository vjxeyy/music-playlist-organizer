# ---------------------------------------------------
# MySQL connection settings, shared by music_organiser.py and setup_database.py
#
# Copy this file to db_config.py and put your MySQL password there.
# db_config.py is listed in .gitignore, so your password is never uploaded.
# ---------------------------------------------------

DB_CONFIG = {
    "host": "localhost",
    "user": "root",          # change if your MySQL username is different
    "password": "root",      # change to your MySQL password
}

DB_NAME = "music_db"     # must match the database name used in music_db.sql
