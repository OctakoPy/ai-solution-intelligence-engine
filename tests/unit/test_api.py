"""Unit tests for the FastAPI endpoints."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from apps.api.engine_cache import get_or_build_engine, reset_cache
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
    assert "Debug (3)" in labels and "Full (78)" in labels


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
async def test_search_returns_why_panel_fields(client: AsyncClient) -> None:
    """Search hits carry the trust-first why-panel evidence payload."""
    await client.post("/api/ingest", json={"max_entries": 12})
    resp = await client.post(
        "/api/search",
        json={"query": "SAP authorization error on FI reports", "top_k": 3},
    )
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert results
    r = results[0]

    # Per-signal breakdown: all seven signals present, non-negative, and
    # summing (approximately) to the displayed confidence.
    breakdown = r["signal_breakdown"]
    assert set(breakdown) == {
        "semantic",
        "error_code",
        "module",
        "environment",
        "success",
        "recency",
        "feedback",
    }
    assert all(v >= 0.0 for v in breakdown.values())
    assert abs(sum(breakdown.values()) - r["confidence"]) < 0.01

    # Prior success counts.
    assert isinstance(r["worked"], int)
    assert isinstance(r["attempted"], int)
    assert r["attempted"] >= 0
    assert r["worked"] <= r["attempted"]

    # Evidence: the hit itself is always first, with matching counts.
    evidence = r["evidence"]
    assert evidence
    assert evidence[0]["id"] == r["id"]
    assert evidence[0]["worked"] == r["worked"]
    assert all("id" in e and "title" in e and "source" in e for e in evidence)

    # Caveats are deterministic strings.
    assert isinstance(r["caveats"], list)
    assert all(isinstance(c, str) for c in r["caveats"])


@pytest.mark.anyio
async def test_search_evidence_includes_duplicate_group_peers(
    client: AsyncClient,
) -> None:
    """Records in the same duplicate_group back each other up as evidence."""
    await client.post("/api/ingest", json={"max_entries": 0})
    # "password reset" surfaces both password_reset_generic records
    # (TIC-1014, TIC-1015), so each hit should list the other as evidence.
    resp = await client.post(
        "/api/search", json={"query": "password reset", "top_k": 5}
    )
    assert resp.status_code == 200
    results = resp.json()["results"]
    grouped = [
        r
        for r in results
        if r["evidence"] and any(e["id"] != r["id"] for e in r["evidence"])
    ]
    assert grouped, "expected at least one hit with cross-record evidence"
    hit = grouped[0]
    peer_ids = [e["id"] for e in hit["evidence"]]
    assert hit["id"] == peer_ids[0], "self must be listed first"
    assert len(peer_ids) >= 2, "grouped hit must list at least one peer"


@pytest.mark.anyio
async def test_search_vague_query_returns_next_best_action(client: AsyncClient) -> None:
    """Below the shared abstain threshold, search returns guidance, not a fix."""
    await client.post("/api/ingest", json={"max_entries": 12})
    resp = await client.post(
        "/api/search",
        json={
            "query": "the custom abap program zreport99 keeps erroring",
            "top_k": 5,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    nba = body["next_best_action"]
    assert nba is not None
    assert nba["action"] in ("ask_context", "escalate_sme")
    assert nba["message"]
    if nba["action"] == "ask_context":
        assert nba["missing_fields"]
    else:
        assert nba["nearest_record_id"]
        assert nba["nearest_record_title"]


@pytest.mark.anyio
async def test_search_confident_query_has_no_next_best_action(
    client: AsyncClient,
) -> None:
    """A strong match must not carry abstain guidance."""
    await client.post("/api/ingest", json={"max_entries": 12})
    resp = await client.post(
        "/api/search",
        json={
            "query": "SAP FI report access denied authorization error",
            "top_k": 3,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    results = body["results"]
    if results and results[0]["confidence"] >= 0.90:
        assert body["next_best_action"] is None
    else:
        # Not confident: an action is acceptable, but never absent-and-silent.
        assert body["next_best_action"] is None or body["next_best_action"][
            "action"
        ] in ("ask_context", "escalate_sme")


@pytest.mark.anyio
async def test_search_context_trap_surfaces_caveat(client: AsyncClient) -> None:
    """Same error code, different environment -> verify-root-cause caveat."""
    await client.post("/api/ingest", json={"max_entries": 0})
    # TIC-3011 is the PROD root cause; querying with the UAT environment
    # must not present it without a warning.
    resp = await client.post(
        "/api/search",
        json={
            "query": "goods receipt posting error",
            "top_k": 5,
            "context": {
                "error_code": "M8149",
                "module": "SAP MM",
                "environment": "UAT",
            },
        },
    )
    assert resp.status_code == 200
    results = resp.json()["results"]
    trap_hits = [r for r in results if r["id"] == "TIC-3011"]
    if trap_hits:
        caveats = " ".join(trap_hits[0]["caveats"])
        assert "Verify root cause" in caveats
        assert "environment" in caveats


@pytest.mark.anyio
async def test_chat_candidates_carry_why_panel_fields(client: AsyncClient) -> None:
    """Chat candidates expose the same evidence payload as search."""
    await client.post("/api/ingest", json={"max_entries": 12})
    resp = await client.post(
        "/api/chat/start",
        json={"query": "SAP authorization error on FI reports", "session_id": "why1"},
    )
    assert resp.status_code == 200
    candidates = resp.json()["candidates"]
    assert candidates
    c = candidates[0]
    assert set(c["signal_breakdown"]) == {
        "semantic",
        "error_code",
        "module",
        "environment",
        "success",
        "recency",
        "feedback",
    }
    assert c["evidence"]
    assert c["evidence"][0]["id"] == c["id"]
    assert isinstance(c["caveats"], list)


@pytest.mark.anyio
async def test_chat_low_confidence_returns_next_best_action(
    client: AsyncClient,
) -> None:
    """Chat abstains through the shared policy and exposes the action."""
    await client.post("/api/ingest", json={"max_entries": 12})
    resp = await client.post(
        "/api/chat/start",
        json={
            "query": "po approval tile missing from fiori launchpad after update",
            "session_id": "nba1",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    if body["next_best_action"] is not None:
        nba = body["next_best_action"]
        assert nba["action"] in ("ask_context", "escalate_sme")
        assert nba["message"]
        # The assistant reply must carry the policy message, not contradict it.
        assistant_text = next(
            t["text"] for t in body["turns"] if t["role"] == "assistant"
        )
        assert (
            any(
                part in assistant_text for part in (nba["message"], nba["message"][:40])
            )
            or "escalate" in assistant_text.lower()
        )


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
async def test_search_accepts_context(client: AsyncClient) -> None:
    await client.post("/api/ingest", json={"max_entries": 12})
    resp = await client.post(
        "/api/search",
        json={
            "query": "SAP authorization error on FI reports",
            "top_k": 5,
            "context": {
                "error_code": "S_RS_COMP",
                "module": "SAP FICO",
                "environment": "PROD",
            },
        },
    )
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert isinstance(results, list)
    assert all(0.0 <= r["confidence"] <= 1.0 for r in results)
    with_context = [r for r in results if r["signals"]]
    assert with_context, "matching context should surface signal badges"


@pytest.mark.anyio
async def test_chat_start_accepts_context(client: AsyncClient) -> None:
    await client.post("/api/ingest", json={"max_entries": 12})
    resp = await client.post(
        "/api/chat/start",
        json={
            "query": "SAP authorization error on FI reports",
            "session_id": "ctx1",
            "context": {"error_code": "S_RS_COMP", "module": "SAP FICO"},
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "turns" in body and "candidates" in body
    assert all(0.0 <= c["confidence"] <= 1.0 for c in body["candidates"])


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
async def test_outcome_endpoint_records_and_updates_count(client: AsyncClient) -> None:
    """POST /api/outcomes persists the outcome and bumps worked_count."""
    await client.post("/api/ingest", json={"max_entries": 3})
    engine = get_or_build_engine(0)
    entry = engine.index.entries[0]
    before = (entry.worked, entry.attempted)
    resp = await client.post(
        "/api/outcomes",
        json={"entry_id": entry.id, "success": True, "note": "fixed it"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["recorded"] is True
    assert body["entry_id"] == entry.id
    assert body["worked_count"] == [before[0] + 1, before[1] + 1]
    assert body["total_outcomes"] == 1


@pytest.mark.anyio
async def test_outcome_endpoint_unknown_id_returns_404(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/outcomes", json={"entry_id": "NOPE", "success": True}
    )
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_outcome_status_reports_learned_state(client: AsyncClient) -> None:
    await client.post("/api/ingest", json={"max_entries": 3})
    engine = get_or_build_engine(0)
    entry_id = engine.index.entries[0].id
    await client.post("/api/outcomes", json={"entry_id": entry_id, "success": False})
    resp = await client.get(f"/api/outcomes/status?entry_id={entry_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["recorded"] is False
    assert body["total_outcomes"] == 1
    assert body["success"] is False


@pytest.mark.anyio
async def test_outcome_learns_across_engines(client: AsyncClient) -> None:
    """The recording engine updates immediately; new engines learn at ingest."""
    await client.post("/api/ingest", json={"max_entries": 3})
    full = get_or_build_engine(0)
    entry_id = full.index.entries[0].id
    recorded = full.index.get(entry_id)
    assert recorded is not None
    base_attempted = recorded.attempted
    resp = await client.post(
        "/api/outcomes",
        json={"entry_id": entry_id, "success": True},
    )
    assert resp.status_code == 200
    # The engine that recorded the outcome reflects it immediately.
    updated = full.index.get(entry_id)
    assert updated is not None
    assert updated.attempted == base_attempted + 1
    # A newly built engine variant applies the same shared memory on ingest.
    fresh = get_or_build_engine(8)
    learned = fresh.index.get(entry_id)
    assert learned is not None
    assert learned.attempted == base_attempted + 1


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
