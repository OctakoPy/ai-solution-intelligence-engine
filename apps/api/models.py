"""Pydantic response/request schemas for the Solution Intelligence API."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

SourceType = Literal["ticket", "sap_note", "sharepoint_doc", "kb_article"]
CheckStage = Literal["stage1", "judge", "duplicate"]
CheckResult = Literal["pass", "flag", "reject"]
Outcome = Literal["added", "rejected", "flagged"]


class HealthResponse(BaseModel):
    """Response for the health endpoint."""

    status: Literal["ok"] = "ok"


class DatasetSize(BaseModel):
    """A single dataset size option."""

    label: str
    size: int


class DatasetSizesResponse(BaseModel):
    """List of available dataset sizes."""

    options: list[DatasetSize]


class GpuLevelResponse(BaseModel):
    """List of available GPU levels."""

    levels: list[str]


class IngestRequest(BaseModel):
    """Request body for /api/ingest."""

    max_entries: int = Field(default=8, ge=1, le=200)


class IngestResponse(BaseModel):
    """Result of an ingestion run."""

    ingested: int
    rejected: int
    total: int


class Check(BaseModel):
    """A single pipeline check for a record."""

    stage: CheckStage
    label: str
    result: CheckResult
    score: float | None = None
    detail: str


class View(BaseModel):
    """One record's view as consumed by the playback animation."""

    id: str
    source_type: SourceType
    source_icon: str
    source_label: str
    title: str
    category: str
    date: str
    description: str
    resolution: str
    outcome: Outcome
    reason: str
    checks: list[Check]
    language: str = "en"


class CategoriesResponse(BaseModel):
    """Unique categories present in the ingested dataset."""

    categories: list[str]


class SourcesResponse(BaseModel):
    """Counts of records per source type."""

    ticket: int
    sap_note: int
    sharepoint_doc: int
    kb_article: int


class IncidentContext(BaseModel):
    """Structured incident context sent alongside a query or chat message."""

    error_code: str | None = None
    module: str | None = None
    environment: str | None = None


class SearchRequest(BaseModel):
    """Request body for /api/search."""

    query: str
    top_k: int = 5
    context: IncidentContext | None = None


class RetrievedSolution(BaseModel):
    """A single retrieved search hit."""

    id: str
    title: str
    source: str
    category: str
    score: float
    confidence: float
    description: str
    resolution: str
    date: str
    language: str = "en"
    english_title: str = ""
    english_description: str = ""
    english_resolution: str = ""
    signals: list[str] = []


class SearchResponse(BaseModel):
    """List of search hits."""

    results: list[RetrievedSolution]


class OutcomeRequest(BaseModel):
    """Request body for POST /api/outcomes."""

    entry_id: str
    success: bool
    note: str = ""
    context: IncidentContext | None = None


class OutcomeResponse(BaseModel):
    """Result of a recorded outcome."""

    recorded: bool
    entry_id: str
    success: bool
    worked_count: list[int]
    total_outcomes: int


class ChatTurn(BaseModel):
    """One message in a chat session."""

    role: Literal["user", "assistant"]
    text: str
    timestamp: str | None = None


class ChatStartRequest(BaseModel):
    """Request body for /api/chat/start."""

    query: str
    session_id: str = "default"
    context: IncidentContext | None = None


class ChatRespondRequest(BaseModel):
    """Request body for /api/chat/respond."""

    session_id: str = "default"
    message: str


class ChatResponse(BaseModel):
    """Response body for both /api/chat/* endpoints."""

    turns: list[ChatTurn]
    candidates: list[RetrievedSolution]


class OverviewRecentRow(BaseModel):
    """One row in the Recent Activity list."""

    source: str
    title: str
    category: str
    status: str
    time_label: str


class OverviewCategoryRow(BaseModel):
    """Top category bar-list row."""

    name: str
    count: int


class OverviewImpactRow(BaseModel):
    """One before/after impact row."""

    label: str
    before: str
    after: str
    delta: str


class OverviewFlaggedRow(BaseModel):
    """One item queued for human review (gray-zone case)."""

    id: str
    title: str
    category: str
    source: str
    reason: str


class OverviewCategoryTimeRow(BaseModel):
    """Average resolution time for a single category."""

    name: str
    avg_time: str


class OverviewResponse(BaseModel):
    """Top-level payload for the Overview page."""

    processed: int
    added: int
    rejected: int
    flagged_count: int = 0
    avg_time: str
    top_categories: list[OverviewCategoryRow]
    before_after: list[OverviewImpactRow]
    recent: list[OverviewRecentRow]
    flagged: list[OverviewFlaggedRow] = []
    resolution_by_category: list[OverviewCategoryTimeRow] = []
