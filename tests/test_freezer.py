"""Tests for the flask-frozen generators.

Locks in which URLs get built into the static site. Regression catch for
the case where collapsing /page/<int:page>/ into index() removes the
auto-freeze of the root /.
"""


def test_index_pages_includes_root(flask_app):
    """The generator must yield '/' so index.html is written at the site root."""
    from app import index_pages
    with flask_app.test_request_context('/'):
        urls = list(index_pages())
    assert '/' in urls


def test_index_pages_includes_numbered_pages(flask_app):
    from app import index_pages
    with flask_app.test_request_context('/'):
        urls = list(index_pages())
    assert '/page/1/' in urls
    assert '/page/2/' in urls


def test_outlet_pages_includes_outlet_root(flask_app, sample_outlet):
    """The generator must yield '/outlet/X/' for each outlet so its index page is built."""
    from app import outlet_pages
    with flask_app.test_request_context('/'):
        urls = list(outlet_pages())
    expected_root = f"/outlet/{sample_outlet['name_encoded']}/"
    assert expected_root in urls


def test_outlet_pages_includes_numbered_pages(flask_app, sample_outlet):
    from app import outlet_pages
    with flask_app.test_request_context('/'):
        urls = list(outlet_pages())
    expected_page_1 = f"/outlet/{sample_outlet['name_encoded']}/page/1/"
    assert expected_page_1 in urls
