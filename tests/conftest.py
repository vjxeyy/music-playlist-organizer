"""Shared fixtures for the Music / Playlist Organiser tests.

Every test runs against a separate database, ``music_db_test``. A guard installed below refuses
any connection to, or SQL that names, the real ``music_db`` database, so running the tests can
never change your own songs and playlists.
"""
import os
import re

import mysql.connector
import pytest

import music_organiser
import setup_database

TEST_DB = "music_db_test"
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_CONFIG = music_organiser.DB_CONFIG          # the one dict shared by both modules


class RealDatabaseTouched(BaseException):
    """Raised by the guard. BaseException, so the program's own error handling can't swallow it."""


# ---------------------------------------------------------------- environment overrides (CI)
for key, env, cast in (("host", "MUSIC_DB_HOST", str), ("port", "MUSIC_DB_PORT", int),
                       ("user", "MUSIC_DB_USER", str), ("password", "MUSIC_DB_PASSWORD", str)):
    if os.environ.get(env):
        DB_CONFIG[key] = cast(os.environ[env])

# ---------------------------------------------------------------- guard
_real_connect = mysql.connector.connect
_REAL_DB = re.compile(r"\bmusic_db\b", re.I)          # matches music_db, not music_db_test


def _guarded_connect(*args, **kwargs):
    if kwargs.get("database") not in (None, TEST_DB):
        raise RealDatabaseTouched(f"tests may only use {TEST_DB}, not {kwargs.get('database')!r}")
    conn = _real_connect(*args, **kwargs)
    real_cursor = conn.cursor

    def cursor(*cargs, **ckwargs):
        cur = real_cursor(*cargs, **ckwargs)
        real_execute = cur.execute

        def execute(operation, params=(), *eargs, **ekwargs):
            if _REAL_DB.search(operation):
                raise RealDatabaseTouched("tests may not run SQL on music_db: " + operation[:80])
            return real_execute(operation, params, *eargs, **ekwargs)

        cur.execute = execute
        return cur

    conn.cursor = cursor
    return conn


mysql.connector.connect = _guarded_connect


@pytest.fixture
def real_db_error():
    return RealDatabaseTouched


# ---------------------------------------------------------------- MySQL availability
def _mysql_reachable():
    try:
        mysql.connector.connect(**DB_CONFIG).close()
        return None
    except mysql.connector.Error as err:
        return setup_database.describe_error(err)


_MYSQL_PROBLEM = _mysql_reachable()


@pytest.fixture(autouse=True)
def _require_mysql_for_db_tests(request):
    if request.node.get_closest_marker("db") and _MYSQL_PROBLEM:
        message = "MySQL is not available for the database tests: " + _MYSQL_PROBLEM
        if os.environ.get("REQUIRE_MYSQL") == "1":
            pytest.fail(message)
        pytest.skip(message)


# ---------------------------------------------------------------- point the program at music_db_test
def _write_sql(path, db_name, encoding="utf-8"):
    with open(os.path.join(PROJECT_DIR, "music_db.sql"), encoding="utf-8") as f:
        sql = f.read().replace("music_db", db_name)
    with open(path, "w", encoding=encoding) as f:
        f.write(sql)
    return str(path)


@pytest.fixture(scope="session")
def test_sql_file(tmp_path_factory):
    return _write_sql(tmp_path_factory.mktemp("sql") / "music_db_test.sql", TEST_DB)


@pytest.fixture
def make_sql_file(tmp_path):
    """Write a copy of music_db.sql for another database name / encoding (for setup tests)."""
    return lambda db_name, encoding="utf-8": _write_sql(tmp_path / f"{db_name}.sql", db_name, encoding)


@pytest.fixture(autouse=True)
def _point_at_test_db(monkeypatch, test_sql_file):
    monkeypatch.setattr(music_organiser, "DB_NAME", TEST_DB)
    monkeypatch.setattr(setup_database, "DB_NAME", TEST_DB)
    monkeypatch.setattr(setup_database, "SQL_FILE", test_sql_file)


@pytest.fixture(scope="session", autouse=True)
def _drop_test_db_at_end():
    yield
    if not _MYSQL_PROBLEM:
        conn = mysql.connector.connect(**DB_CONFIG)
        try:
            conn.cursor().execute(f"DROP DATABASE IF EXISTS {TEST_DB}")
        finally:
            conn.close()


# ---------------------------------------------------------------- database helpers
@pytest.fixture
def fresh_db():
    """Reset music_db_test to the sample data (30 songs, 6 playlists, 30 links)."""
    setup_database.create_database()


@pytest.fixture
def no_db():
    """Make sure music_db_test does not exist (first-run tests)."""
    conn = mysql.connector.connect(**DB_CONFIG)
    try:
        conn.cursor().execute(f"DROP DATABASE IF EXISTS {TEST_DB}")
    finally:
        conn.close()


@pytest.fixture
def q():
    """Run one SQL statement on music_db_test; returns the rows (or lastrowid for writes)."""
    def _q(sql, *args):
        conn = mysql.connector.connect(**DB_CONFIG, database=TEST_DB)
        try:
            cur = conn.cursor()
            cur.execute(sql, args)
            if cur.with_rows:
                return [tuple(row) for row in cur.fetchall()]
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()
    return _q


@pytest.fixture
def song_id(q):
    def _song_id(title):
        rows = q("SELECT song_id FROM Songs WHERE title = %s ORDER BY song_id DESC", title)
        return rows[0][0] if rows else None
    return _song_id


# ---------------------------------------------------------------- driving the program
@pytest.fixture
def run(monkeypatch, capsys):
    """Call a program function with scripted answers to input(); return what it printed.

    Put KeyboardInterrupt in the answers to simulate Ctrl+C. Running out of answers raises
    EOFError, like closing the input stream.
    """
    def _run(func, answers):
        pending = iter(answers)

        def fake_input(prompt=""):
            print(prompt, end="")
            answer = next(pending, EOFError)
            if answer in (EOFError, KeyboardInterrupt):
                raise answer
            print(answer)
            return answer

        monkeypatch.setattr("builtins.input", fake_input)
        capsys.readouterr()
        func()
        return capsys.readouterr().out
    return _run
