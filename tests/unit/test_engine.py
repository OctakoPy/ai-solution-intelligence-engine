"""Tests for the Solution Intelligence Engine core modules."""

import pytest

from solution_intelligence.embeddings import LocalEmbedder
from solution_intelligence.ingestion import (
    AIJudge,
    DuplicateChecker,
    Stage1Filter,
)
from solution_intelligence.models import KnowledgeEntry, StageResult
from solution_intelligence.retrieval import ConfidenceScorer, KnowledgeIndex
from solution_intelligence.sources import TicketConnector, load_entries, load_filtered
import solution_intelligence.analytics as engine_analytics


@pytest.fixture(scope="module")
def dataset(tmp_path_factory):
    """Load a small slice of the real dataset for fast tests."""
    return load_filtered(path="data/knowledge.json", max_total=8)


def make_entry(
    *,
    entry_id="T",
    title="Test issue",
    description="Describe the issue here",
    resolution="Assigned role and confirmed access works now.",
    status="Resolved",
    quality="good",
    access="standard",
    deprecated=False,
    worked=(3, 3),
):
    return KnowledgeEntry(
        id=entry_id,
        source_type="ticket",
        title=title,
        description=description,
        resolution=resolution,
        status=status,
        category="sap_authorization",
        quality_flag=quality,
        access_level=access,
        deprecated_reference=deprecated,
        worked_count=worked,
    )


def test_from_dict_roundtrip():
    raw = {
        "id": "TIC-1",
        "source_type": "ticket",
        "title": "T",
        "description": "D",
        "resolution": "R",
        "status": "Resolved",
        "category": "email",
        "worked_count": [3, 4],
    }
    entry = KnowledgeEntry.from_dict(raw)
    assert entry.worked == 3
    assert entry.attempted == 4
    assert entry.success_rate == 0.75


def test_load_entries_and_connectors():
    entries = load_entries(path="data/knowledge.json")
    tickets = TicketConnector().fetch(entries)
    assert tickets
    assert all(e.source_type == "ticket" for e in tickets)


def test_load_filtered_balanced():
    entries = load_filtered(path="data/knowledge.json", max_total=8)
    assert len(entries) <= 8


def test_stage1_rejects_junk():
    filter = Stage1Filter()
    junk = make_entry(quality="junk")
    result = filter.evaluate(junk)
    assert not result.passed
    assert result.reasons


def test_stage1_accepts_good():
    filter = Stage1Filter()
    good = make_entry()
    result = filter.evaluate(good)
    assert result.passed


def test_ai_judge_scores_good_entry():
    judge = AIJudge()
    good = make_entry(resolution="Checked role in SU01 and assigned missing role.")
    result = judge.evaluate(good)
    assert result.passed
    assert result.overall >= result.threshold
    assert len(result.fields) == 5


def test_ai_judge_rejects_one_off():
    judge = AIJudge()
    bad = make_entry(
        description="One-time request to export historical tickets for audit.",
        resolution="Manual export performed once.",
    )
    result = judge.evaluate(bad)
    assert not result.passed or result.overall < result.threshold


@pytest.mark.slow
def test_embeddings_similarity():
    embedder = LocalEmbedder()
    a = embedder.embed("SAP authorization error on financial reports")
    b = embedder.embed("SAP authorization error on financial reports")
    c = embedder.embed("Printer is jammed and needs new toner")
    assert embedder.similarity(a, b) > embedder.similarity(a, c)


@pytest.mark.slow
def test_embeddings_multilingual_cross_lingual():
    embedder = LocalEmbedder()
    doc_en = embedder.embed("User cannot access FI reports in SAP, authorization error")
    q_bm = embedder.embed(
        "Pengguna tidak boleh buka laporan FI dalam SAP, ralat kebenaran",
        for_query=True,
    )
    q_zh = embedder.embed("用户无法访问SAP财务报告，授权错误", for_query=True)
    unrelated = embedder.embed("The printer is jammed and needs new toner")
    assert embedder.similarity(q_bm, doc_en) > embedder.similarity(q_bm, unrelated)
    assert embedder.similarity(q_zh, doc_en) > embedder.similarity(q_zh, unrelated)


def test_embeddings_multilingual_dims():
    assert LocalEmbedder.dims() == 1024


def test_model_multilingual_fields():
    raw = {
        "id": "TIC-2001",
        "source_type": "ticket",
        "title": "Pengguna tidak boleh buka laporan FI dalam SAP",
        "description": "Ralat kebenaran",
        "resolution": "Berikan peranan Z_FI_REPORT_DISPLAY",
        "language": "bm",
        "english_title": "User cannot open FI reports in SAP",
        "english_description": "Authorization error",
        "english_resolution": "Assign role Z_FI_REPORT_DISPLAY",
    }
    entry = KnowledgeEntry.from_dict(raw)
    assert entry.language == "bm"
    assert entry.english_title == "User cannot open FI reports in SAP"
    assert entry.english_description == "Authorization error"
    assert entry.english_resolution == "Assign role Z_FI_REPORT_DISPLAY"
    d = entry.to_dict()
    assert d["language"] == "bm"
    assert d["english_title"] == "User cannot open FI reports in SAP"


def test_dataset_has_multilingual_entries():
    entries = load_entries(path="data/knowledge.json")
    non_en = [e for e in entries if e.language != "en"]
    assert len(non_en) == 6
    for e in non_en:
        assert e.language in ("bm", "zh")
        assert e.english_title and e.english_description and e.english_resolution


@pytest.mark.slow
def test_knowledge_index_query():
    index = KnowledgeIndex(embedder=LocalEmbedder())
    index.add(make_entry(entry_id="A", title="VPN keeps disconnecting"))
    index.add(make_entry(entry_id="B", title="Printer toner low"))
    results = index.query("vpn connection dropping", top_k=2)
    assert results
    assert results[0].entry.id == "A"


@pytest.mark.slow
def test_duplicate_checker_tiers():
    embedder = LocalEmbedder()
    checker = DuplicateChecker(embedder)
    base = make_entry(entry_id="A", title="SAP report access denied")
    close = make_entry(entry_id="B", title="SAP report access denied for user")
    far = make_entry(entry_id="C", title="Keyboard not responding")
    indexed = [base, far]
    result = checker.evaluate(close, indexed)
    assert result.tier in ("exact_duplicate", "near_duplicate")
    assert far not in [i for i, _ in result.all_scores]


def test_confidence_scorer():
    scorer = ConfidenceScorer()
    strong = make_entry(worked=(9, 9))
    weak = make_entry(worked=(1, 5))
    assert scorer.score(strong, 0.9) > scorer.score(weak, 0.7)


def test_resolution_time_by_category():
    entries = [
        make_entry(entry_id="A", worked=(8, 8)),
        make_entry(entry_id="B", worked=(1, 8)),
        make_entry(entry_id="C", worked=(3, 3)),
    ]
    rows = engine_analytics.resolution_time_by_category(entries)
    assert rows
    name, fmt = rows[0]
    assert name == "sap_authorization"
    assert "min" in fmt or "h" in fmt


@pytest.mark.slow
def test_pipeline_flags_near_duplicate_for_human_review(dataset):
    from solution_intelligence.service import SolutionEngine

    engine = SolutionEngine()
    engine.ingest(dataset)
    assert engine.last_run is not None
    flagged = [s for s in engine.last_run.steps if s.result == StageResult.FLAG]
    assert flagged
    assert all(s.label for s in flagged)


@pytest.mark.slow
def test_pipeline_rejects_duplicates_and_indexes_only_unique():
    """Duplicate entries (exact or near) are rejected, not indexed."""
    from solution_intelligence.service import SolutionEngine

    base = make_entry(
        entry_id="BASE",
        title="VPN drops every morning for Sales team",
        description="Sales users lose VPN connectivity each morning.",
        resolution="Recreated the user profile and reinstalled the VPN client.",
    )
    exact_copy = make_entry(
        entry_id="COPY",
        title="VPN drops every morning for Sales team",
        description="Sales users lose VPN connectivity each morning.",
        resolution="Recreated the user profile and reinstalled the VPN client.",
    )
    near = make_entry(
        entry_id="NEAR",
        title="VPN drops every morning for Sales team in Berlin office",
        description="Sales users in Berlin lose VPN connectivity each morning.",
        resolution="Recreated the user profile and reinstalled the VPN client.",
    )

    engine = SolutionEngine()
    run = engine.ingest([base, exact_copy, near])

    ids_rejected = [e.id for e in run.rejected]
    assert "COPY" in ids_rejected, "exact duplicate must be rejected"
    assert "NEAR" in ids_rejected, "close duplicate must also be rejected"
    assert [e.id for e in run.flagged] == []
    assert [e.id for e in run.indexed] == ["BASE"]
    assert "NEAR" not in [e.id for e in engine.index.entries]

    dup_steps = [s for s in run.steps if s.stage == "duplicate"]
    by_entry = {s.entry.id: s.result for s in dup_steps}
    assert by_entry["COPY"].value == "reject"
    assert by_entry["NEAR"].value == "reject"
    assert by_entry["BASE"].value == "pass"
