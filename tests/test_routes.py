"""Characterization tests: snapshot each route's full HTML response.

On first run (or with UPDATE_SNAPSHOTS=1), the snapshot file is written.
On subsequent runs, the response body must match byte-for-byte.

A refactor of app.py that preserves behavior should leave these green.
"""
import os
import pytest

SNAPSHOT_DIR = os.path.join(os.path.dirname(__file__), "snapshots")
UPDATE = os.environ.get("UPDATE_SNAPSHOTS") == "1"


def _assert_snapshot(name: str, body: bytes):
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    path = os.path.join(SNAPSHOT_DIR, name)
    if UPDATE or not os.path.exists(path):
        with open(path, "wb") as f:
            f.write(body)
        pytest.skip(f"wrote snapshot {name}")
    with open(path, "rb") as f:
        expected = f.read()
    assert body == expected, (
        f"Response for {name} differs from snapshot. "
        f"Re-run with UPDATE_SNAPSHOTS=1 if the change is intentional."
    )


def test_index(client):
    resp = client.get("/")
    assert resp.status_code == 200
    _assert_snapshot("index.html", resp.data)


def test_index_page_2(client):
    resp = client.get("/page/2/")
    assert resp.status_code == 200
    _assert_snapshot("index_page_2.html", resp.data)


def test_index_page_3(client):
    resp = client.get("/page/3/")
    assert resp.status_code == 200
    _assert_snapshot("index_page_3.html", resp.data)


def test_index_custom_per_page(client):
    resp = client.get("/?per_page=5")
    assert resp.status_code == 200
    _assert_snapshot("index_per_page_5.html", resp.data)


def test_index_page_with_custom_per_page(client):
    resp = client.get("/page/2/?per_page=5")
    assert resp.status_code == 200
    _assert_snapshot("index_page_2_per_page_5.html", resp.data)


def test_outlet(client, sample_outlet):
    resp = client.get(f"/outlet/{sample_outlet['name_encoded']}/")
    assert resp.status_code == 200
    _assert_snapshot("outlet.html", resp.data)


def test_outlet_page_2(client, sample_outlet):
    resp = client.get(f"/outlet/{sample_outlet['name_encoded']}/page/2/")
    assert resp.status_code == 200
    _assert_snapshot("outlet_page_2.html", resp.data)


def test_outlet_custom_per_page(client, sample_outlet):
    resp = client.get(f"/outlet/{sample_outlet['name_encoded']}/?per_page=5")
    assert resp.status_code == 200
    _assert_snapshot("outlet_per_page_5.html", resp.data)


def test_outlet_page_with_custom_per_page(client, sample_outlet):
    resp = client.get(f"/outlet/{sample_outlet['name_encoded']}/page/2/?per_page=5")
    assert resp.status_code == 200
    _assert_snapshot("outlet_page_2_per_page_5.html", resp.data)


def test_article(client, sample_article):
    url = (
        f"/article/{sample_article['outlet_name_encoded']}"
        f"/{sample_article['date_published']}"
        f"/{sample_article['title_encoded']}/"
    )
    resp = client.get(url)
    assert resp.status_code == 200
    _assert_snapshot("article.html", resp.data)


def test_mentions(client):
    resp = client.get("/mentions/")
    assert resp.status_code == 200
    _assert_snapshot("mentions.html", resp.data)
