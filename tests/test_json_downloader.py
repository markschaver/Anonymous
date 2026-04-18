"""Unit tests for json-downloader.py.

Uses importlib because the module filename contains a hyphen.
"""
import importlib.util
import json as json_lib
import os
import sys
from datetime import date

import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


def _load_module():
    path = os.path.join(PROJECT_ROOT, "json-downloader.py")
    spec = importlib.util.spec_from_file_location("json_downloader", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["json_downloader"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def jd():
    return _load_module()


# ---- encode_phrase ---------------------------------------------------------

def test_encode_phrase_strips_and_encodes_spaces(jd):
    assert jd.encode_phrase("  anonymous source  \n") == "anonymous+source"


def test_encode_phrase_percent_encodes_specials(jd):
    assert jd.encode_phrase("a&b") == "a%26b"


# ---- get_phrase_file -------------------------------------------------------

def test_get_phrase_file_even_day(jd):
    assert jd.get_phrase_file(date(2025, 6, 14)) == jd.PHRASES_EVEN


def test_get_phrase_file_odd_day(jd):
    assert jd.get_phrase_file(date(2025, 6, 13)) == jd.PHRASES_ODD


# ---- get_url ---------------------------------------------------------------

def test_get_url_contains_all_parts(jd):
    url = jd.get_url("anonymous+source", "&cx=FAKE_ID", "&key=FAKE_KEY")
    assert url.startswith("https://www.googleapis.com/customsearch/v1?q=anonymous+source")
    assert "&cx=FAKE_ID" in url
    assert "&key=FAKE_KEY" in url
    assert "&dateRestrict=d2" in url
    assert "&hl=en" in url
    assert "&alt=json" in url


def test_get_url_preserves_query_duplication(jd):
    """Pin current behavior: the query appears twice — once as q=<q>, once as &<q>."""
    url = jd.get_url("foo", "", "")
    assert url.count("foo") == 2


def test_get_url_concatenation_order(jd):
    """Pin the full concatenation order to catch accidental reordering."""
    url = jd.get_url("QQ", "ID", "KEY")
    assert url == (
        "https://www.googleapis.com/customsearch/v1?q=QQ"
        "ID&dateRestrict=d2&QQ&hl=enKEY&alt=json"
    )


# ---- get_json --------------------------------------------------------------

def test_get_json_writes_response_to_file(jd, tmp_path, monkeypatch):
    class FakeResp:
        def json(self_inner):
            return {"items": [{"title": "x"}]}

    monkeypatch.setattr(jd.requests, "get", lambda url: FakeResp())
    out_dir = str(tmp_path) + "/"
    jd.get_json("https://example.com/search", output_dir=out_dir)
    files = list(tmp_path.iterdir())
    assert len(files) == 1
    assert files[0].name.endswith(".json")
    with open(files[0]) as f:
        assert json_lib.load(f) == {"items": [{"title": "x"}]}


def test_get_json_passes_url_to_requests(jd, tmp_path, monkeypatch):
    captured = []

    class FakeResp:
        def json(self_inner):
            return {}

    def fake_get(url):
        captured.append(url)
        return FakeResp()

    monkeypatch.setattr(jd.requests, "get", fake_get)
    jd.get_json("https://example.com/probe", output_dir=str(tmp_path) + "/")
    assert captured == ["https://example.com/probe"]


# ---- pause_search ----------------------------------------------------------

def test_pause_search_calls_sleep_with_value_in_range(jd, monkeypatch):
    calls = []
    monkeypatch.setattr(jd, "sleep", lambda s: calls.append(s))
    jd.pause_search(sleep_range=(5, 7))
    assert len(calls) == 1
    assert 5 <= calls[0] <= 7


def test_pause_search_zero_range(jd, monkeypatch):
    calls = []
    monkeypatch.setattr(jd, "sleep", lambda s: calls.append(s))
    jd.pause_search(sleep_range=(0, 0))
    assert calls == [0]


# ---- load_config -----------------------------------------------------------

def test_load_config_reads_id_and_key(jd, tmp_path):
    cfg = tmp_path / "c.ini"
    cfg.write_text("[Configuration]\nid = &cx=ABC\nkey = &key=XYZ\n")
    google_id, google_key = jd.load_config(path=str(cfg))
    assert google_id == "&cx=ABC"
    assert google_key == "&key=XYZ"


# ---- main (integration) ----------------------------------------------------

def test_main_iterates_phrases_and_calls_get_json(jd, tmp_path, monkeypatch):
    phrases_file = tmp_path / "phrases.txt"
    phrases_file.write_text("anonymous source\nunnamed sources\n")

    monkeypatch.setattr(jd, "load_config", lambda: ("ID", "KEY"))
    monkeypatch.setattr(jd, "get_phrase_file", lambda today: str(phrases_file))
    monkeypatch.setattr(jd, "pause_search", lambda: None)

    calls = []
    monkeypatch.setattr(jd, "get_json", lambda url: calls.append(url))

    jd.main()

    assert len(calls) == 2
    assert "anonymous+source" in calls[0]
    assert "unnamed+sources" in calls[1]


def test_main_skips_no_phrases(jd, tmp_path, monkeypatch):
    phrases_file = tmp_path / "empty.txt"
    phrases_file.write_text("")

    monkeypatch.setattr(jd, "load_config", lambda: ("ID", "KEY"))
    monkeypatch.setattr(jd, "get_phrase_file", lambda today: str(phrases_file))
    monkeypatch.setattr(jd, "pause_search", lambda: None)

    calls = []
    monkeypatch.setattr(jd, "get_json", lambda url: calls.append(url))

    jd.main()
    assert calls == []
