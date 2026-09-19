# ruff: noqa: I001
from __future__ import annotations

import re
from typing import Any

import httpx

from corporate_rfq.opensearch_catalog import OpenSearchTransportError


_INDEX_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


class OpenSearchHttpReadOnlyTransport:
    """HTTP implementation of the read-only OpenSearch search transport.

    Authentication, TLS, proxying and base URL are deliberately configured on
    the injected httpx.Client by the composition root. This class owns no
    credentials and exposes no mutation methods.
    """

    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    def search(self, *, index: str, body: dict[str, Any]) -> dict[str, Any]:
        if not _INDEX_RE.fullmatch(index):
            raise OpenSearchTransportError("Invalid OpenSearch index name")

        try:
            response = self._client.post(f"/{index}/_search", json=body)
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise OpenSearchTransportError("OpenSearch HTTP search failed") from exc

        if not isinstance(payload, dict):
            raise OpenSearchTransportError("OpenSearch response must be a JSON object")

        return payload
