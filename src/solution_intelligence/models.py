"""Core data models for the Solution Intelligence Engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class StageResult(Enum):
    """Outcome of an ingestion stage for a single entry."""

    PASS = "pass"
    REJECT = "reject"
    FLAG = "flag"


@dataclass
class KnowledgeEntry:
    """A single knowledge record ingested from any source system."""

    id: str
    source_type: str
    title: str
    description: str
    resolution: str = ""
    status: str = "Resolved"
    category: str = "unknown"
    access_level: str = "standard"
    date: str = ""
    demo_tag: str | None = None
    duplicate_group: str | None = None
    similarity_tier: str = "unique"
    quality_flag: str = "good"
    deprecated_reference: bool = False
    worked_count: tuple[int, int] = (0, 0)
    error_code: str | None = None
    module: str | None = None
    environment: str | None = None
    feedback_score: float = 0.0
    language: str = "en"
    english_title: str = ""
    english_description: str = ""
    english_resolution: str = ""

    @property
    def worked(self) -> int:
        """Times this solution has worked successfully."""
        return self.worked_count[0]

    @property
    def attempted(self) -> int:
        """Times this solution has been attempted."""
        return self.worked_count[1]

    @property
    def success_rate(self) -> float:
        """Historical success rate as a fraction (0..1)."""
        if self.attempted <= 0:
            return 0.0
        return self.worked / self.attempted

    @property
    def full_text(self) -> str:
        """Combined text used for embedding and similarity."""
        return f"{self.title}\n{self.description}\n{self.resolution}"

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "KnowledgeEntry":
        """Build a KnowledgeEntry from a raw source dict."""
        worked_count = raw.get("worked_count", [])
        if isinstance(worked_count, list) and len(worked_count) >= 2:
            worked = int(worked_count[0])
            attempted = int(worked_count[1])
        else:
            worked = 0
            attempted = 0
        return cls(
            id=str(raw.get("id", "")),
            source_type=str(raw.get("source_type", "ticket")),
            title=str(raw.get("title", "")),
            description=str(raw.get("description", "")),
            resolution=str(raw.get("resolution", "")),
            status=str(raw.get("status", "Resolved")),
            category=str(raw.get("category", "unknown")),
            access_level=str(raw.get("access_level", "standard")),
            date=str(raw.get("date", "")),
            demo_tag=raw.get("demo_tag"),
            duplicate_group=raw.get("duplicate_group"),
            similarity_tier=str(raw.get("similarity_tier", "unique")),
            quality_flag=str(raw.get("quality_flag", "good")),
            deprecated_reference=bool(raw.get("deprecated_reference", False)),
            worked_count=(worked, attempted),
            error_code=raw.get("error_code"),
            module=raw.get("module"),
            environment=raw.get("environment"),
            feedback_score=float(raw.get("feedback_score", 0.0)),
            language=str(raw.get("language", "en")),
            english_title=str(raw.get("english_title", "")),
            english_description=str(raw.get("english_description", "")),
            english_resolution=str(raw.get("english_resolution", "")),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialise back to a plain dict."""
        return {
            "id": self.id,
            "source_type": self.source_type,
            "title": self.title,
            "description": self.description,
            "resolution": self.resolution,
            "status": self.status,
            "category": self.category,
            "access_level": self.access_level,
            "date": self.date,
            "demo_tag": self.demo_tag,
            "duplicate_group": self.duplicate_group,
            "similarity_tier": self.similarity_tier,
            "quality_flag": self.quality_flag,
            "deprecated_reference": self.deprecated_reference,
            "worked_count": [self.worked, self.attempted],
            "error_code": self.error_code,
            "module": self.module,
            "environment": self.environment,
            "feedback_score": self.feedback_score,
            "language": self.language,
            "english_title": self.english_title,
            "english_description": self.english_description,
            "english_resolution": self.english_resolution,
        }


@dataclass
class Stage1Result:
    """Outcome of the rule-based Stage 1 filter."""

    entry: KnowledgeEntry
    passed: bool
    reasons: list[str] = field(default_factory=list)


@dataclass
class JudgeField:
    """A single field assessed by the AI judge."""

    name: str
    label: str
    score: float  # 0..1
    explanation: str = ""


@dataclass
class JudgeResult:
    """Outcome of the AI-based quality judge."""

    entry: KnowledgeEntry
    fields: list[JudgeField] = field(default_factory=list)
    overall: float = 0.0  # 0..1 confidence
    passed: bool = False
    threshold: float = 0.6


@dataclass
class DuplicateResult:
    """Outcome of the duplicate/similarity check."""

    entry: KnowledgeEntry
    tier: str  # exact_duplicate | near_duplicate | unique
    best_match_id: str | None = None
    best_match_title: str | None = None
    best_score: float = 0.0
    all_scores: list[tuple[str, float]] = field(default_factory=list)


@dataclass
class PipelineStep:
    """A single visual step in the ingestion animation."""

    entry: KnowledgeEntry
    stage: str  # source | stage1 | judge | duplicate
    label: str
    result: StageResult
    score: float | None = None


@dataclass
class PipelineRun:
    """Full record of entries flowing through the pipeline."""

    steps: list[PipelineStep] = field(default_factory=list)
    ingested: list[KnowledgeEntry] = field(default_factory=list)
    rejected: list[KnowledgeEntry] = field(default_factory=list)
    # Entries kept for review (near-duplicates): ingested but deliberately
    # NOT added to the knowledge index.
    flagged: list[KnowledgeEntry] = field(default_factory=list)

    def add(self, step: PipelineStep) -> None:
        """Append a pipeline step."""
        self.steps.append(step)

    @property
    def indexed(self) -> list[KnowledgeEntry]:
        """Entries that belong in the knowledge index (ingested minus flagged)."""
        flagged_ids = {e.id for e in self.flagged}
        return [e for e in self.ingested if e.id not in flagged_ids]


@dataclass
class RetrievedSolution:
    """A single retrieved candidate with trust metadata."""

    entry: KnowledgeEntry
    score: float  # similarity 0..1
    confidence: float  # overall quality 0..1
    duplicate_of: str | None = None
    signals: list[str] = field(default_factory=list)

    @property
    def combined_score(self) -> float:
        """Blend similarity and confidence for ranking."""
        return round(0.7 * self.score + 0.3 * self.confidence, 3)
