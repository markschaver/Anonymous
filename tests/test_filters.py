"""Unit tests for Jinja template filters registered in app.py."""


def test_datetimeformat_default(flask_app):
    with flask_app.app_context():
        from app import datetimeformat
        assert datetimeformat("2025-06-13") == "June 13, 2025"


def test_datetimeformat_custom_format(flask_app):
    with flask_app.app_context():
        from app import datetimeformat
        assert datetimeformat("2025-06-13", "%Y/%m/%d") == "2025/06/13"


def test_datetimeformat_falsy_returns_empty(flask_app):
    """A single NULL date shouldn't 404 the whole listing page."""
    with flask_app.app_context():
        from app import datetimeformat
        assert datetimeformat("") == ''
        assert datetimeformat(None) == ''


def test_clean_content_strips_and_replaces(flask_app):
    with flask_app.app_context():
        from app import clean_content
        raw = "  hello\nworld\r<br>foo<b>...</b>bar  "
        out = clean_content(raw)
        assert "\n" not in out
        assert "\r" not in out
        assert "<br>" not in out
        assert "<b>...</b>" not in out
        assert out.startswith("hello")


def test_clean_content_removes_x01(flask_app):
    """chr(0x01) should be stripped."""
    with flask_app.app_context():
        from app import clean_content
        out = clean_content("a\x01b")
        assert "\x01" not in out


def test_clean_content_extra_bold_collapses_to_space(flask_app):
    """`</b>...<b>` runs collapse to a single space, no stray \\x01."""
    with flask_app.app_context():
        from app import clean_content
        raw = "foo</b>middle<b>bar"
        out = clean_content(raw)
        assert out == "foo bar"
        assert "\x01" not in out


def test_clean_content_falsy_returns_empty(flask_app):
    """Empty content shouldn't 404 the whole listing page."""
    with flask_app.app_context():
        from app import clean_content
        assert clean_content("") == ''
        assert clean_content(None) == ''


def test_plus_for_spaces(flask_app):
    with flask_app.app_context():
        from app import plus_for_spaces
        assert plus_for_spaces("New York Times") == "New+York+Times"
        assert plus_for_spaces("A&B") == "A%26B"
