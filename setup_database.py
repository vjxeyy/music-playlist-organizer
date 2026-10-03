# ---------------------------------------------------
# Project: Music / Playlist Organiser
# Creates (or resets) the music_db database by running music_db.sql.
# Usage: python setup_database.py
# ---------------------------------------------------

import os
import re
import sys

import mysql.connector
from mysql.connector import errorcode

try:
    from db_config import DB_CONFIG, DB_NAME
except ModuleNotFoundError:
    sys.exit("db_config.py not found. Copy db_config.example.py to db_config.py "
             "and put your MySQL password in it.")

SQL_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "music_db.sql")

# Matches "USE x", "CREATE DATABASE x ..." and "DROP DATABASE IF EXISTS x" and captures x.
DATABASE_STATEMENT = re.compile(
    r"^(?:USE|(?:CREATE|DROP)\s+DATABASE(?:\s+IF\s+(?:NOT\s+)?EXISTS)?)\s+`?(\w+)`?", re.I)


def is_yes(answer):
    return answer.strip().lower() in ("y", "yes")


def describe_error(err):
    """Turn an error into a message that says what to fix."""
    if not isinstance(err, mysql.connector.Error):
        return str(err)
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        return "MySQL rejected the username/password. Update DB_CONFIG in db_config.py."
    if err.errno in (errorcode.CR_CONN_HOST_ERROR, errorcode.CR_CONNECTION_ERROR,
                     errorcode.CR_UNKNOWN_HOST):
        return (f"Cannot connect to MySQL on '{DB_CONFIG['host']}'. "
                "Make sure MySQL Server is installed and running.")
    if err.errno == errorcode.ER_NO_SUCH_TABLE:
        return (f"{err.msg}. Run 'python setup_database.py' to rebuild the tables "
                "(this replaces the data with the sample songs and playlists).")
    return f"MySQL error {err.errno}: {err.msg}"


def read_statements(path):
    """Split an SQL script into single statements.

    Lines starting with -- are comments and statements end with ';'.
    This simple splitter assumes no ';' appears inside a quoted value,
    which is true for music_db.sql. "utf-8-sig" also accepts files that
    an editor saved with a byte-order mark.
    """
    with open(path, encoding="utf-8-sig") as f:
        lines = [line for line in f if not line.strip().startswith("--")]
    return [stmt.strip() for stmt in "".join(lines).split(";") if stmt.strip()]


def database_exists():
    db = mysql.connector.connect(**DB_CONFIG)
    try:
        cur = db.cursor()
        cur.execute("SELECT SCHEMA_NAME FROM information_schema.SCHEMATA "
                    "WHERE SCHEMA_NAME = %s", (DB_NAME,))
        return cur.fetchone() is not None
    finally:
        db.close()


def create_database():
    """Run music_db.sql: drops music_db if present and recreates it with sample data."""
    statements = read_statements(SQL_FILE)
    # Never drop or create a database other than the one the program uses.
    for statement in statements:
        match = DATABASE_STATEMENT.match(statement)
        if match and match.group(1).lower() != DB_NAME.lower():
            raise RuntimeError(f"music_db.sql does not create '{DB_NAME}' (it uses "
                               f"'{match.group(1)}'). Make DB_NAME in db_config.py match it.")

    db = mysql.connector.connect(**DB_CONFIG)
    try:
        cur = db.cursor()
        for statement in statements:
            cur.execute(statement)
        db.commit()
    finally:
        db.close()


def main():
    try:
        if database_exists():
            print(f"The database '{DB_NAME}' already exists.")
            answer = input("Reset it? All songs and playlists will be replaced "
                           "with the sample data. (y/n): ")
            if not is_yes(answer):
                print("Nothing changed.")
                return
        create_database()
    except (mysql.connector.Error, RuntimeError) as err:
        print("\n❌ " + describe_error(err) + "\n")
        return
    print(f"✅ '{DB_NAME}' is ready with the sample songs and playlists.")


if __name__ == "__main__":
    # Lets emoji print safely on older Windows consoles and when output is redirected.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
