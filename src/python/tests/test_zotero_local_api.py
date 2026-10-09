import json
import pytest
from research import zotero_local_api as api


class Response:
    def __init__(self, status, headers=None, body=b""):
        self.status, self.headers, self.body = status, headers or {}, body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.body


def test_update_authorizes_and_guards_item_version(monkeypatch):
    calls = []
    responses = [
        Response(200, {"Zotero-Server-ID": "server"}),
        Response(200, body=json.dumps({"version": 7}).encode()),
        Response(200, body=b'{"key":"one-time-key"}'),
        Response(204),
    ]

    def fake(req, timeout):
        calls.append(req)
        return responses.pop(0)

    monkeypatch.setattr(api, "urlopen", fake)
    assert api.ZoteroLocalAPI().update_item(
        "38QV4IUR", {"DOI": "10.1234/example"}
    ) == ["DOI"]
    assert [req.get_method() for req in calls] == [
        "GET",
        "GET",
        "POST",
        "PATCH",
    ]
    headers = {k.lower(): v for k, v in calls[3].header_items()}
    assert headers["if-unmodified-since-version"] == "7"
    assert headers["zotero-api-key"] == "one-time-key"
    assert json.loads(calls[3].data) == {"DOI": "10.1234/example"}


def test_update_rejects_unsupported_fields_before_network(monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("unexpected network call")

    monkeypatch.setattr(api, "urlopen", fail)
    with pytest.raises(
        api.ZoteroLocalAPIError, match="Unsupported Zotero fields"
    ):
        api.ZoteroLocalAPI().update_item("38QV4IUR", {"itemType": "book"})


def test_update_requires_server_id_before_authorizing(monkeypatch):
    calls = []

    def fake(req, timeout):
        calls.append(req)
        return Response(200)

    monkeypatch.setattr(api, "urlopen", fake)
    with pytest.raises(api.ZoteroLocalAPIError, match="Zotero 10"):
        api.ZoteroLocalAPI().update_item(
            "38QV4IUR", {"title": "Corrected title"}
        )
    assert len(calls) == 1
