"""Unit tests for Jinja template filters registered in app.py.

These pin down current behavior (including the \\x01-vs-\\1 quirk in
clean_content, see app.py:148) so a refactor preserves identical output.
"""
import pytest
from werkzeug.exceptions import NotFound


def test_datetimeformat_default(flask_app):
    with flask_app.app_context():
        from app import datetimeformat
        assert datetimeformat("2025-06-13") == "June 13, 2025"


def test_datetimeformat_custom_format(flask_app):
    with flask_app.app_context():
        from app import datetimeformat
        assert datetimeformat("2025-06-13", "%Y/%m/%d") == "2025/06/13"


def test_datetimeformat_falsy_aborts(flask_app):
    with flask_app.app_context():
        from app import datetimeformat
        with pytest.raises(NotFound):
            datetimeformat("")
        with pytest.raises(NotFound):
            datetimeformat(None)


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


def test_clean_content_extra_bold_current_behavior(flask_app):
    """The `extra_bold` regex collapses </b>...<b> runs.

    Note: app.py line 148 uses a non-raw "\\1 " replacement, so the
    "backreference" is actually chr(0x01) + space. And because the
    chr(0x01) strip on line 147 runs BEFORE this substitution, the
    \\x01 injected here survives into the output. This test pins
    the current (likely-buggy) behavior.
    """
    with flask_app.app_context():
        from app import clean_content
        raw = "foo</b>middle<b>bar"
        out = clean_content(raw)
        assert out == "foo\x01 bar"


def test_clean_content_falsy_aborts(flask_app):
    with flask_app.app_context():
        from app import clean_content
        with pytest.raises(NotFound):
            clean_content("")
        with pytest.raises(NotFound):
            clean_content(None)


def test_plus_for_spaces(flask_app):
    with flask_app.app_context():
        from app import plus_for_spaces
        assert plus_for_spaces("New York Times") == "New+York+Times"
        assert plus_for_spaces("A&B") == "A%26B"
