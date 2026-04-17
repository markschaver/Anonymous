"""Tests for the DB/helper functions in app.py.

Runs helpers inside a test request context so g.db is set up the way
before_request does it. Pins return shapes and a few concrete values
from the live anon.db.
"""


def test_query_db_returns_list_of_dicts(flask_app):
    with flask_app.test_request_context("/"):
        flask_app.preprocess_request()
        from app import query_db
        rows = query_db("SELECT name, url FROM outlets ORDER BY name LIMIT 3")
        assert isinstance(rows, list)
        assert len(rows) == 3
        for row in rows:
            assert set(row.keys()) == {"name", "url"}


def test_query_db_one_returns_single_dict(flask_app):
    with flask_app.test_request_context("/"):
        flask_app.preprocess_request()
        from app import query_db
        row = query_db("SELECT count(*) AS n FROM anon", one=True)
        assert isinstance(row, dict)
        assert "n" in row
        assert row["n"] > 0


def test_get_outlet_url_roundtrip(flask_app, sample_outlet):
    with flask_app.test_request_context("/"):
        flask_app.preprocess_request()
        from app import get_outlet_url
        assert get_outlet_url(sample_outlet["name_encoded"]) == sample_outlet["url"]


def test_get_outlet_name_roundtrip(flask_app, sample_outlet):
    # get_outlet_name opens its own connection; it doesn't need a request ctx.
    with flask_app.test_request_context("/"):
        from app import get_outlet_name
        result = get_outlet_name(sample_outlet["url"])
        # Currently returns plus-encoded form of the name.
        assert result == sample_outlet["name_encoded"]


def test_get_total_anon_pages_positive(flask_app):
    with flask_app.test_request_context("/"):
        from app import get_total_anon_pages
        assert get_total_anon_pages() >= 1


def test_get_total_outlet_pages_positive(flask_app, sample_outlet):
    with flask_app.test_request_context("/"):
        from app import get_total_outlet_pages
        assert get_total_outlet_pages(sample_outlet["url"]) >= 1


def test_get_page_items_defaults(flask_app):
    with flask_app.test_request_context("/"):
        from app import get_page_items, PER_PAGE
        page, per_page, offset = get_page_items()
        assert page == 1
        assert per_page == PER_PAGE
        assert offset == 0


def test_get_page_items_with_query(flask_app):
    with flask_app.test_request_context("/?page=3&per_page=5"):
        from app import get_page_items
        page, per_page, offset = get_page_items()
        assert page == 3
        assert per_page == 5
        assert offset == 10
