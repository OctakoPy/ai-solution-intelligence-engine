"""Unit tests for the FastAPI endpoints."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from apps.api.engine_cache import reset_cache
from apps.api.main import app


@pytest.fixture(autouse=True)
def _reset_engine() -> None:
    """Clear the per-request engine cache before each test."""
    reset_cache()


@pytest.fixture()
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest.mark.anyio
async def test_health(client: AsyncClient) -> None:
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.anyio
async def test_dataset_sizes(client: AsyncClient) -> None:
    resp = await client.get("/api/dataset/sizes")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["options"]) == 3
    labels = [o["label"] for o in data["options"]]
    assert "Debug (3)" in labels and "Full (76)" in labels


@pytest.mark.anyio
async def test_gpu_levels(client: AsyncClient) -> None:
    resp = await client.get("/api/gpu/levels")
    assert resp.status_code == 200
    assert len(resp.json()["levels"]) == 3


@pytest.mark.anyio
async def test_ingest(client: AsyncClient) -> None:
    resp = await client.post("/api/ingest", json={"max_entries": 3})
    assert resp.status_code == 200
    body = resp.json()
    assert body["ingested"] >= 0
    assert body["rejected"] >= 0
    assert body["total"] == body["ingested"] + body["rejected"]


@pytest.mark.anyio
async def test_pipeline_views(client: AsyncClient) -> None:
    await client.post("/api/ingest", json={"max_entries": 3})
    resp = await client.get("/api/pipeline/views?max_entries=3")
    assert resp.status_code == 200
    views = resp.json()
    assert isinstance(views, list)
    assert views, "expected at least one view for the Debug(3) dataset"
    v = views[0]
    for key in (
        "id",
        "source_type",
        "source_icon",
        "source_label",
        "title",
        "category",
        "date",
        "description",
        "resolution",
        "outcome",
        "reason",
        "checks",
    ):
        assert key in v, f"view missing key {key}"
    assert v["outcome"] in ("added", "rejected", "flagged")
    assert all(c["stage"] in ("stage1", "judge", "duplicate") for c in v["checks"])


@pytest.mark.anyio
async def test_categories(client: AsyncClient) -> None:
    await client.post("/api/ingest", json={"max_entries": 3})
    resp = await client.get("/api/categories?max_entries=3")
    assert resp.status_code == 200
    assert isinstance(resp.json()["categories"], list)


@pytest.mark.anyio
async def test_sources(client: AsyncClient) -> None:
    await client.post("/api/ingest", json={"max_entries": 3})
    resp = await client.get("/api/sources?max_entries=3")
    assert resp.status_code == 200
    body = resp.json()
    for key in ("ticket", "sap_note", "sharepoint_doc", "kb_article"):
        assert key in body


@pytest.mark.anyio
async def test_search(client: AsyncClient) -> None:
    await client.post("/api/ingest", json={"max_entries": 3})
    resp = await client.post(
        "/api/search", json={"query": "SAP authorization", "top_k": 3}
    )
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert isinstance(results, list)
    if results:
        r = results[0]
        for key in (
            "id",
            "title",
            "source",
            "category",
            "score",
            "confidence",
            "description",
            "resolution",
            "date",
        ):
            assert key in r


@pytest.mark.anyio
async def test_search_surfaces_multilingual(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/search",
        json={
            "query": "user cannot access financial reports in sap, authorization error",
            "top_k": 10,
        },
    )
    assert resp.status_code == 200
    results = resp.json()["results"]
    by_lang = {r["language"] for r in results}
    assert "bm" in by_lang
    bm = next(r for r in results if r["language"] == "bm")
    assert bm["english_title"] and bm["english_resolution"]
    assert bm["english_description"]


@pytest.mark.anyio
async def test_chat_start(client: AsyncClient) -> None:
    await client.post("/api/ingest", json={"max_entries": 3})
    resp = await client.post(
        "/api/chat/start",
        json={"query": "SAP authorization error", "session_id": "t1"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "turns" in body and "candidates" in body


@pytest.mark.anyio
async def test_chat_respond(client: AsyncClient) -> None:
    await client.post("/api/ingest", json={"max_entries": 3})
    await client.post(
        "/api/chat/start",
        json={"query": "SAP authorization error", "session_id": "t2"},
    )
    resp = await client.post(
        "/api/chat/respond",
        json={"session_id": "t2", "message": "more details please"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["turns"]) >= 2


@pytest.mark.anyio
async def test_chat_low_confidence_escalates(client: AsyncClient) -> None:
    await client.post("/api/ingest", json={"max_entries": 12})
    resp = await client.post(
        "/api/chat/start",
        json={
            "query": "po approval tile missing from fiori launchpad after update",
            "session_id": "t3",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert any(
        "confident match" in t["text"] or "escalate" in t["text"] for t in body["turns"]
    )


@pytest.mark.anyio
async def test_analytics_overview(client: AsyncClient) -> None:
    await client.post("/api/ingest", json={"max_entries": 3})
    resp = await client.get("/api/analytics/overview?max_entries=3")
    assert resp.status_code == 200
    body = resp.json()
    for key in (
        "processed",
        "added",
        "rejected",
        "avg_time",
        "top_categories",
        "before_after",
        "recent",
        "flagged",
        "resolution_by_category",
    ):
        assert key in body


@pytest.mark.anyio
async def test_analytics_overview_flagged(client: AsyncClient) -> None:
    await client.post("/api/ingest", json={"max_entries": 12})
    resp = await client.get("/api/analytics/overview?max_entries=12")
    assert resp.status_code == 200
    body = resp.json()
    assert body["flagged"], "expected near-duplicates to be flagged"
    assert all(row["reason"] for row in body["flagged"])
    assert body["resolution_by_category"]


@pytest.mark.anyio
async def test_full_dataset_duplicate_policy(client: AsyncClient) -> None:
    """On the full dataset: exact dups rejected, near dups flagged, rest added."""
    await client.post("/api/ingest", json={"max_entries": 76})
    resp = await client.get("/api/pipeline/views?max_entries=76")
    assert resp.status_code == 200
    views = resp.json()
    outcomes = {v["outcome"] for v in views}
    assert "flagged" in outcomes, "expected near-duplicates flagged on full dataset"
    assert "rejected" in outcomes, "expected exact-duplicates rejected on full dataset"
    assert "added" in outcomes
    for v in views:
        dup_checks = [c for c in v["checks"] if c["stage"] == "duplicate"]
        if v["outcome"] == "flagged":
            assert dup_checks and dup_checks[-1]["result"] == "flag"
        if v["outcome"] == "rejected":
            assert v["checks"][-1]["result"] == "reject"
            if dup_checks:
                assert dup_checks[-1]["result"] == "reject"
