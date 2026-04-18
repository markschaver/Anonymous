"""Unit tests for json-processor.py.

The module has a hyphen in its name so we load it via importlib. Each
test that touches the database uses its own temporary SQLite file with
the anon table schema mirroring the live DB.
"""
import importlib.util
import os
import sqlite3
import sys
import tempfile
from datetime import date

import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


def _load_module():
    path = os.path.join(PROJECT_ROOT, "json-processor.py")
    spec = importlib.util.spec_from_file_location("json_processor", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["json_processor"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def jp():
    return _load_module()


@pytest.fixture()
def temp_db():
    """A fresh SQLite file with the live anon schema."""
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


# ---- normalize_source ------------------------------------------------------

def test_normalize_source_maps_nytimes(jp):
    assert jp.normalize_source("foo.nytimes.com") == "www.nytimes.com"


def test_normalize_source_maps_ap(jp):
    assert jp.normalize_source("apnews.com") == "www.apnews.com"


def test_normalize_source_keeps_unknown_host(jp):
    assert jp.normalize_source("example.com") == "example.com"


def test_normalize_source_is_idempotent(jp):
    """Running twice doesn't cascade (canonical form shouldn't re-match)."""
    once = jp.normalize_source("foo.cnn.com")
    twice = jp.normalize_source(once)
    assert once == twice == "www.cnn.com"


# ---- extract_publish_date --------------------------------------------------

def test_extract_publish_date_newsarticle(jp):
    item = {"pagemap": {"newsarticle": [{"datepublished": "2025-06-13T12:00:00Z"}]}}
    assert jp.extract_publish_date(item) == "2025-06-13T12:00:00Z"


def test_extract_publish_date_metatag_article_published(jp):
    item = {"pagemap": {"metatags": [{"article:published": "2025-06-14"}]}}
    assert jp.extract_publish_date(item) == "2025-06-14"


def test_extract_publish_date_metatag_article_published_time(jp):
    item = {"pagemap": {"metatags": [{"article:published_time": "2025-06-15T08:00Z"}]}}
    assert jp.extract_publish_date(item) == "2025-06-15T08:00Z"


def test_extract_publish_date_last_match_wins(jp):
    """When several paths resolve, the LAST one in PUB_DATE_PATHS wins
    (preserves the original stacked try/except/pass semantics)."""
    item = {
        "pagemap": {
            "newsarticle": [{"datepublished": "2025-01-01"}],   # first
            "metatags": [{"dc.date": "2025-12-31"}],             # last in list
        }
    }
    assert jp.extract_publish_date(item) == "2025-12-31"


def test_extract_publish_date_none_when_missing(jp):
    assert jp.extract_publish_date({"pagemap": {}}) is None
    assert jp.extract_publish_date({}) is None


# ---- is_valid_date ---------------------------------------------------------

def test_is_valid_date_accepts_date_object(jp):
    assert jp.is_valid_date(date(2025, 1, 1)) is True


def test_is_valid_date_accepts_iso_string(jp):
    assert jp.is_valid_date("2025-06-13") is True


def test_is_valid_date_accepts_unix_epoch_int(jp):
    assert jp.is_valid_date(1700000000) is True


def test_is_valid_date_accepts_unix_epoch_string(jp):
    assert jp.is_valid_date("1700000000") is True


def test_is_valid_date_rejects_empty(jp):
    assert jp.is_valid_date("") is False
    assert jp.is_valid_date(None) is False


def test_is_valid_date_rejects_garbage_string(jp):
    assert jp.is_valid_date("not a date") is False


# ---- update_database -------------------------------------------------------

def test_update_database_inserts_valid_entry(jp, temp_db):
    conn, _ = temp_db
    fields = [
        "www.example.com", "anonymous source", "Test title",
        "https://example.com/x", "some <b>anonymous</b> content",
        "2025-06-13",
    ]
    jp.update_database(conn, date(2025, 6, 14), fields)
    rows = conn.execute("SELECT source, title, date_entered, date_published FROM anon").fetchall()
    assert rows == [("www.example.com", "Test title", "2025-06-14", "2025-06-13")]


def test_update_database_skips_missing_bold_tag(jp, temp_db):
    conn, _ = temp_db
    fields = [
        "www.example.com", "x", "T", "https://example.com/y",
        "snippet without bold", "2025-06-13",
    ]
    jp.update_database(conn, date(2025, 6, 14), fields)
    assert conn.execute("SELECT count(*) FROM anon").fetchone()[0] == 0


def test_update_database_skips_invalid_publish_date(jp, temp_db, tmp_path, monkeypatch):
    conn, _ = temp_db
    monkeypatch.setattr(jp, "INVALID_LOG_PATH", str(tmp_path / "invalid.log"))
    fields = [
        "www.example.com", "x", "T", "https://example.com/z",
        "has <b>bold</b>", "garbage-date",
    ]
    jp.update_database(conn, date(2025, 6, 14), fields)
    assert conn.execute("SELECT count(*) FROM anon").fetchone()[0] == 0


# ---- process_search_results (integration) ----------------------------------

def _sample_results(num_items=1, date_path=("metatags", 0, "article:published_time")):
    """Build a minimal Google CSE response that exercises the full pipeline."""
    item = {
        "displayLink": "foo.nytimes.com",
        "title": "Test Article",
        "link": "https://www.nytimes.com/2025/06/13/test.html",
        "htmlSnippet": "An <b>anonymous</b> source said ...",
        "pagemap": {},
    }
    # Nest the date at the requested path.
    cursor = item["pagemap"]
    for key in date_path[:-1]:
        if isinstance(key, int):
            cursor.append({})
            cursor = cursor[key]
        else:
            cursor.setdefault(key, [] if isinstance(date_path[1], int) else {})
            cursor = cursor[key]
    # Simpler: hand-build the structure.
    item["pagemap"] = {"metatags": [{"article:published_time": "2025-06-13T12:00Z"}]}
    return {
        "queries": {"request": [{"count": num_items, "searchTerms": "anonymous"}]},
        "items": [item for _ in range(num_items)],
    }


def test_process_search_results_inserts_item(jp, temp_db):
    conn, _ = temp_db
    data = _sample_results(num_items=1)
    jp.process_search_results(conn, date(2025, 6, 14), data)
    rows = conn.execute("SELECT source, title, date_published FROM anon").fetchall()
    assert rows == [("www.nytimes.com", "Test Article", "2025-06-13")]


def test_process_search_results_skips_entries_without_dates(jp, temp_db):
    """Regression test for the 'item_published leak' bug in the original.
    An item with no resolvable date must be skipped, not inherit a neighbor's date."""
    conn, _ = temp_db
    good = {
        "displayLink": "www.nytimes.com",
        "title": "Dated",
        "link": "https://nytimes.com/a",
        "htmlSnippet": "<b>x</b>",
        "pagemap": {"metatags": [{"article:published_time": "2025-01-01"}]},
    }
    dateless = {
        "displayLink": "www.nytimes.com",
        "title": "Undated",
        "link": "https://nytimes.com/b",
        "htmlSnippet": "<b>x</b>",
        "pagemap": {},
    }
    data = {
        "queries": {"request": [{"count": 2, "searchTerms": "x"}]},
        "items": [good, dateless],
    }
    jp.process_search_results(conn, date(2025, 6, 14), data)
    rows = conn.execute("SELECT title, date_published FROM anon ORDER BY title").fetchall()
    assert rows == [("Dated", "2025-01-01")]


def test_process_search_results_washingtonpost_url_date(jp, temp_db):
    """URLs containing YYYY/MM/DD override whatever pagemap said."""
    conn, _ = temp_db
    item = {
        "displayLink": "www.washingtonpost.com",
        "title": "WaPo article",
        "link": "https://www.washingtonpost.com/politics/2024/03/15/foo/",
        "htmlSnippet": "<b>x</b>",
        "pagemap": {"metatags": [{"article:published_time": "2099-01-01"}]},  # ignored
    }
    data = {"queries": {"request": [{"count": 1, "searchTerms": "x"}]}, "items": [item]}
    jp.process_search_results(conn, date(2025, 6, 14), data)
    row = conn.execute("SELECT date_published FROM anon").fetchone()
    assert row == ("2024-03-15",)


def test_process_search_results_trims_datetime_to_date(jp, temp_db):
    """Dates like '2025-06-13T12:00:00Z' should be stored as '2025-06-13'."""
    conn, _ = temp_db
    data = _sample_results(num_items=1)
    jp.process_search_results(conn, date(2025, 6, 14), data)
    row = conn.execute("SELECT date_published FROM anon").fetchone()
    assert row == ("2025-06-13",)


def test_process_search_results_skips_on_missing_structure(jp, temp_db):
    conn, _ = temp_db
    jp.process_search_results(conn, date(2025, 6, 14), {"not": "what we expect"})
    assert conn.execute("SELECT count(*) FROM anon").fetchone()[0] == 0
