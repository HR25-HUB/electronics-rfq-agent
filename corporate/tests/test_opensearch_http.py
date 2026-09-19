from __future__ import annotations

import json

import httpx
import pytest

from corporate_rfq.opensearch_catalog import OpenSearchTransportError
from corporate_rfq.opensearch_http import OpenSearchHttpReadOnlyTransport


def test_http_transport_posts_only_to_search_endpoint() -> None:
    body = {"size": 1, "query": {"match": {"sku": {"query": "S203C16"}}}}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/gamm_catalog_products/_search"
        assert json.loads(request.content) == body
        return httpx.Response(200, json={"hits": {"hits": []}})

    with httpx.Client(
        base_url="https://opensearch.invalid",
        transport=httpx.MockTransport(handler),
    ) as client:
        transport = OpenSearchHttpReadOnlyTransport(client)
        response = transport.search(index="gamm_catalog_products", body=body)

    assert response == {"hits": {"hits": []}}


@pytest.mark.parametrize(
    "index",
    [
        "../secret",
        "Products",
        "/absolute",
        "index?pretty=true",
        "index name",
    ],
)
def test_http_transport_rejects_unsafe_index_names(index: str) -> None:
    with httpx.Client(base_url="https://opensearch.invalid") as client:
        transport = OpenSearchHttpReadOnlyTransport(client)
        with pytest.raises(OpenSearchTransportError):
            transport.search(index=index, body={"query": {"match_all": {}}})


def test_http_transport_maps_non_success_to_transport_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"error": "unavailable"}, request=request)

    with httpx.Client(
        base_url="https://opensearch.invalid",
        transport=httpx.MockTransport(handler),
    ) as client:
        transport = OpenSearchHttpReadOnlyTransport(client)
        with pytest.raises(OpenSearchTransportError):
            transport.search(
                index="gamm_catalog_products",
                body={"query": {"match_all": {}}},
            )


def test_http_transport_rejects_non_object_json_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=["unexpected"], request=request)

    with httpx.Client(
        base_url="https://opensearch.invalid",
        transport=httpx.MockTransport(handler),
    ) as client:
        transport = OpenSearchHttpReadOnlyTransport(client)
        with pytest.raises(OpenSearchTransportError):
            transport.search(
                index="gamm_catalog_products",
                body={"query": {"match_all": {}}},
            )


def test_public_http_transport_surface_is_read_only() -> None:
    forbidden = ("create", "update", "delete", "write", "save", "upsert", "mutate", "bulk")
    public_names = {
        name for name in dir(OpenSearchHttpReadOnlyTransport) if not name.startswith("_")
    }

    assert public_names == {"search"}
    assert not any(name.startswith(forbidden) for name in public_names)
