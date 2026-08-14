"""Tests for the publish window.

The site renders only recently collected examples while anon.db keeps the
full archive. These lock in that the window is applied everywhere that
feeds the frozen site: counts, entry queries, outlet lists and the
freezer's URL generators.
"""
import os
import sqlite3

import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


@pytest.fixture(scope="module")
def db():
    conn = sqlite3.connect(os.path.join(PROJECT_ROOT, "anon.db"))
    yield conn
    conn.close()


def test_window_start_is_iso_and_in_the_past(flask_app):
    import app as A
    from datetime import datetime

    cutoff = A.window_start()
    parsed = datetime.strptime(cutoff, "%Y-%m-%d")
    assert (datetime.now() - parsed).days == A.WINDOW_DAYS


def test_archive_is_larger_than_window(db, flask_app):
    """The DB must keep everything; the window is a view, not a delete."""
    import app as A

    archive = db.execute("SELECT count(*) FROM anon").fetchone()[0]
    window = db.execute(A.COUNT_ANON, (A.window_start(),)).fetchone()[0]
    assert window < archive, "window should exclude older rows"
    assert window > 0, "window should not be empty"


def test_no_entry_older_than_cutoff_is_published(db, flask_app):
    """The entry query must not leak rows from outside the window."""
    import app as A

    cutoff = A.window_start()
    rows = db.execute(
        f"SELECT anon.{A.WINDOW_COLUMN} FROM anon "
        f"LEFT OUTER JOIN outlets ON anon.source = outlets.url "
        f"WHERE anon.{A.WINDOW_COLUMN} >= ?",
        (cutoff,),
    ).fetchall()
    assert rows, "expected some in-window rows"
    assert all(r[0] >= cutoff for r in rows)


def test_count_by_source_is_windowed(db, flask_app, sample_outlet):
    import app as A

    cutoff = A.window_start()
    windowed = db.execute(
        A.COUNT_ANON_BY_SOURCE, (cutoff, sample_outlet["url"])
    ).fetchone()[0]
    all_time = db.execute(
        "SELECT count(*) FROM anon WHERE source = ?", (sample_outlet["url"],)
    ).fetchone()[0]
    assert 0 < windowed <= all_time


def test_outlets_in_use_excludes_quiet_outlets(db, flask_app):
    """Outlets with nothing in the window get no pages at all."""
    import app as A

    cutoff = A.window_start()
    in_use = {r[0] for r in db.execute(A.OUTLET_URLS_IN_USE, (cutoff,))}
    all_outlets = {r[0] for r in db.execute("SELECT DISTINCT url FROM outlets")}
    assert in_use, "expected at least one active outlet"
    assert in_use <= all_outlets
    for url in all_outlets - in_use:
        n = db.execute(A.COUNT_ANON_BY_SOURCE, (cutoff, url)).fetchone()[0]
        assert n == 0, f"{url} was excluded but has {n} in-window rows"


def test_index_generator_covers_exactly_the_window(flask_app):
    """Generated /page/N/ URLs must match the windowed row count."""
    import app as A
    import math

    with flask_app.test_request_context("/"):
        urls = list(A.index_pages())
        total = A.get_total_anon_pages()
    numbered = [u for u in urls if u.startswith("/page/")]
    assert len(numbered) == total
    assert f"/page/{total}/" in urls
    assert f"/page/{total + 1}/" not in urls


def test_outlet_generator_only_yields_active_outlets(flask_app, db):
    import app as A

    cutoff = A.window_start()
    with flask_app.test_request_context("/"):
        urls = list(A.outlet_pages())
    active = db.execute(A.OUTLET_URLS_IN_USE, (cutoff,)).fetchall()
    roots = [u for u in urls if u.count("/") == 3]
    assert len(roots) == len(active)


def test_window_days_is_configurable(monkeypatch):
    """ANON_WINDOW_DAYS drives the cutoff so the window can be retuned."""
    import importlib
    import app as A

    monkeypatch.setenv("ANON_WINDOW_DAYS", "7")
    reloaded = importlib.reload(A)
    try:
        assert reloaded.WINDOW_DAYS == 7
    finally:
        monkeypatch.delenv("ANON_WINDOW_DAYS", raising=False)
        importlib.reload(A)


def test_invalid_window_column_is_rejected(monkeypatch):
    """The column is interpolated into SQL, so it must be allowlisted."""
    import importlib
    import app as A

    monkeypatch.setenv("ANON_WINDOW_COLUMN", "date_entered; DROP TABLE anon")
    try:
        with pytest.raises(ValueError):
            importlib.reload(A)
    finally:
        monkeypatch.delenv("ANON_WINDOW_COLUMN", raising=False)
        importlib.reload(A)
