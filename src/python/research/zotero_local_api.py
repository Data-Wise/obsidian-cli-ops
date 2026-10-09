"""Authorized writes to the Zotero 10+ local API."""

from __future__ import annotations

import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

_ITEM_KEY = re.compile(r"^[23456789ABCDEFGHIJKLMNPQRSTUVWXYZ]{8}$")
_ALLOWED_FIELDS = frozenset(
    {
        "title",
        "date",
        "DOI",
        "url",
        "publicationTitle",
        "volume",
        "issue",
        "pages",
        "abstractNote",
        "shortTitle",
        "language",
        "journalAbbreviation",
        "series",
        "seriesTitle",
        "place",
        "publisher",
        "edition",
        "number",
        "extra",
    }
)


class ZoteroLocalAPIError(RuntimeError):
    """A safe, user-readable local API or validation failure."""


class ZoteroLocalAPI:
    """Update existing Zotero items through Zotero's authorized local API.

    This intentionally does not write to Zotero's SQLite database. Zotero 10+
    prompts the user to authorize each first-time write, and local API writes
    remain ordinary Zotero changes that can sync normally.
    """

    def __init__(self, timeout: int = 120):
        self.base_url = "http://127.0.0.1:23119"
        self.timeout = timeout

    def _request(self, method: str, path: str, *, headers=None, body=None):
        request_headers = {"Host": "localhost"}
        request_headers.update(headers or {})
        data = None if body is None else json.dumps(body).encode("utf-8")
        if data is not None:
            request_headers["Content-Type"] = "application/json"
        request = Request(
            self.base_url + path,
            data=data,
            headers=request_headers,
            method=method,
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                payload = response.read()
                return response.status, dict(response.headers.items()), payload
        except HTTPError as exc:
            raise ZoteroLocalAPIError(
                f"Zotero local API returned HTTP {exc.code} ({exc.reason})."
            ) from exc
        except URLError as exc:
            if isinstance(exc.reason, TimeoutError):
                raise ZoteroLocalAPIError(
                    "Timed out waiting for Zotero's local API authorization "
                    "or response."
                ) from exc
            raise ZoteroLocalAPIError(
                "Cannot reach Zotero's local API at 127.0.0.1:23119; "
                "check that Zotero is open and Settings → Advanced → "
                "Allow other applications to communicate with Zotero "
                "is enabled."
            ) from exc
        except TimeoutError as exc:
            raise ZoteroLocalAPIError(
                "Timed out waiting for Zotero's local API authorization "
                "or response."
            ) from exc

    def update_item(self, key: str, updates: dict[str, str]) -> list[str]:
        if not _ITEM_KEY.fullmatch(key):
            raise ZoteroLocalAPIError(
                "Item key must be an 8-character Zotero key."
            )
        if not isinstance(updates, dict) or not updates:
            raise ZoteroLocalAPIError(
                "Provide at least one metadata field to update."
            )
        if len(updates) > len(_ALLOWED_FIELDS):
            raise ZoteroLocalAPIError("Too many fields were supplied.")
        unknown = sorted(set(updates) - _ALLOWED_FIELDS)
        if unknown:
            raise ZoteroLocalAPIError(
                "Unsupported Zotero fields: " + ", ".join(unknown)
            )
        if any(not isinstance(value, str) for value in updates.values()):
            raise ZoteroLocalAPIError(
                "Metadata values must be strings; use an empty string to "
                "clear a field."
            )

        server_id = None
        status, headers, payload = self._request("GET", "/api/")
        server_id = next(
            (
                value
                for name, value in headers.items()
                if name.lower() == "zotero-server-id"
            ),
            None,
        )
        if status != 200 or not server_id:
            raise ZoteroLocalAPIError(
                "Zotero 10+ local API is required for authorized item updates."
            )

        item_path = f"/api/users/0/items/{quote(key, safe='')}"
        status, _, payload = self._request(
            "GET", item_path, headers={"Zotero-Server-ID": server_id}
        )
        if status != 200:
            raise ZoteroLocalAPIError(
                f"Could not retrieve Zotero item {key} (HTTP {status})."
            )
        try:
            item = json.loads(payload.decode("utf-8"))
            version = item.get("version") or item.get("data", {}).get(
                "version"
            )
        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
            AttributeError,
        ) as exc:
            raise ZoteroLocalAPIError(
                "Zotero returned invalid item data."
            ) from exc
        if not version:
            raise ZoteroLocalAPIError(
                "Zotero did not return an item version; refusing an "
                "unguarded update."
            )

        status, _, payload = self._request(
            "POST",
            "/api/local/authorize",
            headers={"Zotero-Server-ID": server_id},
            body={"appName": "Obsidian CLI Ops"},
        )
        try:
            api_key = json.loads(payload.decode("utf-8")).get("key")
        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
            AttributeError,
        ) as exc:
            raise ZoteroLocalAPIError(
                "Zotero did not return write authorization."
            ) from exc
        if status != 200 or not api_key:
            raise ZoteroLocalAPIError(
                "Zotero write authorization was not granted."
            )

        self._request(
            "PATCH",
            item_path,
            headers={
                "Zotero-Server-ID": server_id,
                "Zotero-API-Key": api_key,
                "If-Unmodified-Since-Version": str(version),
            },
            body=updates,
        )
        return sorted(updates)
