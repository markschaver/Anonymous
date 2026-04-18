"""Unit tests for dupes.py.

Each test uses its own temporary SQLite file with the anon table schema
mirroring the live DB.
"""
import os
import sqlite3
import sys
import tempfile

import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import dupes


@pytest.fixture()
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    conn = sqlite3.connect(path)
    conn.execute(
        "CREATE TABLE anon ("
        "source TEXT, phrase TEXT, title TEXT, link TEXT, "
        "content TEXT, date_entered TEXT, date_published TEXT"
        ")"
    )
    conn.commit()
    yield conn, path
    conn.close()
    os.unlink(path)


def _insert(conn, rows):
    conn.executemany(
        "INSERT INTO anon (source, phrase, title, link, content, date_entered, date_published) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        rows,
    )
    conn.commit()


def _links(conn):
    return [r[0] for r in conn.execute("SELECT link FROM anon ORDER BY ROWID").fetchall()]


# ---- delete_duplicates -----------------------------------------------------

def test_delete_duplicates_by_content_keeps_lowest_rowid(temp_db):
    conn, _ = temp_db
    _insert(conn, [
        ("src", "p", "T1", "https://a/1", "same", "2025-01-01", "2025-01-01"),
        ("src", "p", "T2", "https://a/2", "same", "2025-01-02", "2025-01-02"),
        ("src", "p", "T3", "https://a/3", "diff", "2025-01-03", "2025-01-03"),
    ])
    dupes.delete_duplicates(conn, "content")
    assert _links(conn) == ["https://a/1", "https://a/3"]


def test_delete_duplicates_respects_source_grouping(temp_db):
    """Same content from different sources is not a duplicate."""
    conn, _ = temp_db
    _insert(conn, [
        ("srcA", "p", "T", "https://a/1", "same", "2025-01-01", "2025-01-01"),
        ("srcB", "p", "T", "https://b/1", "same", "2025-01-02", "2025-01-02"),
    ])
    dupes.delete_duplicates(conn, "content")
    assert _links(conn) == ["https://a/1", "https://b/1"]


def test_delete_duplicates_by_title(temp_db):
    conn, _ = temp_db
    _insert(conn, [
        ("src", "p", "Shared", "https://a/1", "c1", "2025-01-01", "2025-01-01"),
        ("src", "p", "Shared", "https://a/2", "c2", "2025-01-02", "2025-01-02"),
    ])
    dupes.delete_duplicates(conn, "title")
    assert _links(conn) == ["https://a/1"]


def test_delete_duplicates_by_link(temp_db):
    conn, _ = temp_db
    _insert(conn, [
        ("src", "p", "T1", "https://a/1", "c1", "2025-01-01", "2025-01-01"),
        ("src", "p", "T2", "https://a/1", "c2", "2025-01-02", "2025-01-02"),
    ])
    dupes.delete_duplicates(conn, "link")
    assert _links(conn) == ["https://a/1"]


def test_delete_duplicates_prints_error_on_bad_column(temp_db, capsys):
    conn, _ = temp_db
    dupes.delete_duplicates(conn, "does_not_exist")
    out = capsys.readouterr().out
    assert "didn't work" in out


# ---- delete_blocklisted ----------------------------------------------------

def test_delete_blocklisted_removes_like_fragment(temp_db):
    conn, _ = temp_db
    _insert(conn, [
        ("src", "p", "T", "https://apnews.com/author/jane-doe", "c", "2025-01-01", "2025-01-01"),
        ("src", "p", "T", "https://apnews.com/article/real-news", "c", "2025-01-01", "2025-01-01"),
    ])
    dupes.delete_blocklisted(conn)
    assert _links(conn) == ["https://apnews.com/article/real-news"]


def test_delete_blocklisted_removes_exact_match(temp_db):
    conn, _ = temp_db
    _insert(conn, [
        ("src", "p", "T", "https://www.propublica.org/", "c", "2025-01-01", "2025-01-01"),
        ("src", "p", "T", "https://www.propublica.org/article/x", "c", "2025-01-01", "2025-01-01"),
    ])
    dupes.delete_blocklisted(conn)
    assert _links(conn) == ["https://www.propublica.org/article/x"]


def test_delete_blocklisted_preserves_unrelated_rows(temp_db):
    conn, _ = temp_db
    _insert(conn, [
        ("src", "p", "T", "https://example.com/kept", "c", "2025-01-01", "2025-01-01"),
    ])
    dupes.delete_blocklisted(conn)
    assert _links(conn) == ["https://example.com/kept"]


def test_delete_blocklisted_removes_reuters_legal_exact_but_not_subpaths(temp_db):
    """/legal/ is in EXACT, so '/legal/foo' should survive."""
    conn, _ = temp_db
    _insert(conn, [
        ("src", "p", "T", "https://www.reuters.com/legal/", "c", "2025-01-01", "2025-01-01"),
        ("src", "p", "T", "https://www.reuters.com/legal/foo", "c", "2025-01-01", "2025-01-01"),
    ])
    dupes.delete_blocklisted(conn)
    assert _links(conn) == ["https://www.reuters.com/legal/foo"]


def test_delete_blocklisted_covers_many_patterns(temp_db):
    """Smoke test: rows matching several different patterns all get deleted."""
    conn, _ = temp_db
    _insert(conn, [
        ("src", "p", "T", "https://www.cnn.com/videos/2025/xyz", "c", "2025-01-01", "2025-01-01"),
        ("src", "p", "T", "https://www.nytimes.com/topic/politics", "c", "2025-01-01", "2025-01-01"),
        ("src", "p", "T", "https://finance.yahoo.com/quote/AAPL", "c", "2025-01-01", "2025-01-01"),
        ("src", "p", "T", "https://www.reuters.com/technology/ai", "c", "2025-01-01", "2025-01-01"),
        ("src", "p", "T", "https://example.com/kept", "c", "2025-01-01", "2025-01-01"),
    ])
    dupes.delete_blocklisted(conn)
    assert _links(conn) == ["https://example.com/kept"]


# ---- main (integration) ----------------------------------------------------

def test_main_runs_dedup_and_blocklist(temp_db):
    conn, path = temp_db
    _insert(conn, [
        ("src", "p", "T1", "https://ok.com/a", "dup", "2025-01-01", "2025-01-01"),
        ("src", "p", "T2", "https://ok.com/b", "dup", "2025-01-02", "2025-01-02"),
        ("src", "p", "T3", "https://www.cnn.com/videos/x", "c", "2025-01-03", "2025-01-03"),
        ("src", "p", "T4", "https://ok.com/c", "unique", "2025-01-04", "2025-01-04"),
    ])
    conn.close()
    dupes.main(db_path=path)
    conn2 = sqlite3.connect(path)
    try:
        links = [r[0] for r in conn2.execute("SELECT link FROM anon ORDER BY ROWID").fetchall()]
    finally:
        conn2.close()
    assert links == ["https://ok.com/a", "https://ok.com/c"]


# ---- data sanity -----------------------------------------------------------

def test_blocklist_has_no_duplicates():
    assert len(dupes.BLOCKLIST_LIKE) == len(set(dupes.BLOCKLIST_LIKE))
    assert len(dupes.BLOCKLIST_EXACT) == len(set(dupes.BLOCKLIST_EXACT))


def test_dedup_columns_are_known():
    assert set(dupes.DEDUP_COLUMNS) <= {"content", "title", "link", "source", "phrase"}
