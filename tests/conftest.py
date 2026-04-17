"""Shared pytest fixtures.

Sets up the Flask test client and picks deterministic fixture rows
from the existing anon.db so route tests reference stable data.
"""
import os
import sys
import sqlite3
from urllib.parse import quote_plus

import pytest

# Make the project root importable and ensure the DB path resolves
# regardless of where pytest is invoked from.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, PROJECT_ROOT)


@pytest.fixture(scope="session", autouse=True)
def _chdir_project_root():
    """connect_db() uses a relative path 'anon.db', so tests must run from project root."""
    prev = os.getcwd()
    os.chdir(PROJECT_ROOT)
    yield
    os.chdir(prev)


@pytest.fixture(scope="session")
def flask_app():
    import app as app_module
    app_module.app.config["TESTING"] = True
    return app_module.app


@pytest.fixture()
def client(flask_app):
    return flask_app.test_client()


@pytest.fixture(scope="session")
def sample_outlet():
    """Pick a deterministic outlet that has at least 2 pages of results."""
    conn = sqlite3.connect(os.path.join(PROJECT_ROOT, "anon.db"))
    cur = conn.cursor()
    cur.execute(
        "SELECT o.name, o.url, COUNT(a.source) AS n "
        "FROM outlets o JOIN anon a ON a.source = o.url "
        "GROUP BY o.url HAVING n > 30 ORDER BY o.name LIMIT 1"
    )
    row = cur.fetchone()
    conn.close()
    assert row is not None, "Need at least one outlet with >30 anon rows"
    name, url, _ = row
    return {"name": name, "url": url, "name_encoded": quote_plus(name)}


@pytest.fixture(scope="session")
def sample_article(sample_outlet):
    """Pick a deterministic article row for the chosen outlet."""
    conn = sqlite3.connect(os.path.join(PROJECT_ROOT, "anon.db"))
    cur = conn.cursor()
    cur.execute(
        "SELECT source, title, date_published FROM anon "
        "WHERE source = ? AND date_published IS NOT NULL "
        "ORDER BY date_published DESC, title LIMIT 1",
        (sample_outlet["url"],),
    )
    row = cur.fetchone()
    conn.close()
    assert row is not None
    source, title, date_published = row
    return {
        "source": source,
        "title": title,
        "title_encoded": quote_plus(title),
        "date_published": date_published,
        "outlet_name_encoded": sample_outlet["name_encoded"],
    }
