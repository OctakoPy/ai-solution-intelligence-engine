"""Resolution Memory: confirmed-outcome write-back for the learning loop.

Every confirmed outcome — a consultant marking a recommendation as worked or
not worked — is appended to a persistent, human-readable JSON log and folded
back into the affected records' ``worked_count`` as a *recomputed delta* over
the base dataset. Because the delta is always recomputed from the log, the
loop is idempotent: re-ingesting the static dataset never double-counts past
outcomes, and deleting the log file resets the engine to its pristine state.

The learning flows into ranking with no extra ranking code: ``worked_count``
feeds ``success_rate``, which is one of the seven deterministic signals in
the outcome-aware confidence score (weight 0.20). A confirmed failure
demotes a candidate on the next search and a confirmed success boosts it —
positive and negative learning from the same mechanism.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from solution_intelligence.models import KnowledgeEntry
from solution_intelligence.retrieval import IncidentContext

# The learning log lives next to the dataset and the embedding cache. It is
# runtime user data, not a source artifact: gitignored, and safe to delete to
# reset the engine's learned state.
DEFAULT_MEMORY_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "resolution_memory.json"
)


@dataclass(frozen=True)
class OutcomeRecord:
    """One confirmed outcome appended to the resolution memory log."""

    entry_id: str
    success: bool
    note: str = ""
    error_code: str | None = None
    module: str | None = None
    environment: str | None = None
    timestamp: str = ""
    source: str = "api"

    def to_dict(self) -> dict[str, Any]:
        """Serialise for the JSON log."""
        return {
            "entry_id": self.entry_id,
            "success": self.success,
            "note": self.note,
            "error_code": self.error_code,
            "module": self.module,
            "environment": self.environment,
            "timestamp": self.timestamp,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> OutcomeRecord:
        """Rebuild a record from a log entry."""
        return cls(
            entry_id=str(raw.get("entry_id", "")),
            success=bool(raw.get("success", False)),
            note=str(raw.get("note", "")),
            error_code=raw.get("error_code"),
            module=raw.get("module"),
            environment=raw.get("environment"),
            timestamp=str(raw.get("timestamp", "")),
            source=str(raw.get("source", "api")),
        )


class ResolutionMemory:
    """Persistent log of confirmed outcomes, applied as recomputed deltas.

    Args:
        path: JSON log location. Defaults to
            ``data/resolution_memory.json``; pass ``None`` for an
            in-memory-only store (evaluations, throwaway tests).
    """

    def __init__(self, path: str | Path | None = DEFAULT_MEMORY_PATH) -> None:
        self.path = Path(path) if path is not None else None
        self._records: list[OutcomeRecord] = []
        # Pristine worked_count per entry id, captured the first time the
        # entry is adjusted. Deltas are always applied on top of this base,
        # which is what makes repeated applies idempotent.
        self._base_worked: dict[str, tuple[int, int]] = {}
        self._load()

    def record(
        self,
        entry_id: str,
        success: bool,
        *,
        note: str = "",
        context: IncidentContext | None = None,
        source: str = "api",
        timestamp: str | None = None,
    ) -> OutcomeRecord:
        """Append a confirmed outcome and persist the log.

        Args:
            entry_id: The knowledge record the outcome is about.
            success: Whether the recommended resolution actually worked.
            note: Optional free-text context from the consultant.
            context: Optional incident context captured with the outcome.
            source: Where the outcome came from (``"api"``, ``"ui"``).
            timestamp: Optional ISO-8601 timestamp to store instead of the
                current time (used by the demo seed so recency stays
                deterministic relative to seed time).

        Returns:
            The stored record.
        """
        record = OutcomeRecord(
            entry_id=entry_id,
            success=success,
            note=note,
            error_code=context.error_code if context else None,
            module=context.module if context else None,
            environment=context.environment if context else None,
            timestamp=(
                timestamp
                if timestamp is not None
                else datetime.now(timezone.utc).isoformat(timespec="seconds")
            ),
            source=source,
        )
        self._records.append(record)
        self._save()
        return record

    def clear(self) -> None:
        """Drop every recorded outcome and persist the empty log.

        Intended for reseeding at startup, before any :meth:`apply` has
        folded deltas into live entries. It does not un-apply deltas that
        were already folded into entries earlier in the process.
        """
        self._records.clear()
        self._save()

    def entry_deltas(self) -> dict[str, tuple[int, int]]:
        """Recompute per-entry ``(worked, attempted)`` deltas from the log.

        Returns:
            A mapping of entry id to how many worked/attempted counts should
            be added to the record's base ``worked_count``.
        """
        deltas: dict[str, tuple[int, int]] = {}
        for record in self._records:
            d_worked, d_attempted = deltas.get(record.entry_id, (0, 0))
            deltas[record.entry_id] = (
                d_worked + (1 if record.success else 0),
                d_attempted + 1,
            )
        return deltas

    def stats(self) -> dict[str, Any]:
        """Aggregate confirmed-outcome stats for the dashboard.

        Returns:
            A mapping with ``total``, ``worked``, ``rejected``,
            ``success_rate`` (0..1), ``entries_learned`` (distinct entry
            ids with at least one outcome), and ``last_outcome_at`` (ISO
            timestamp of the newest record, or ``None`` when empty).
        """
        total = len(self._records)
        worked = sum(1 for record in self._records if record.success)
        rejected = total - worked
        return {
            "total": total,
            "worked": worked,
            "rejected": rejected,
            "success_rate": round(worked / total, 3) if total else 0.0,
            "entries_learned": len({record.entry_id for record in self._records}),
            "last_outcome_at": self._records[-1].timestamp if total else None,
        }

    def apply(self, entries: Iterable[KnowledgeEntry]) -> int:
        """Fold past outcomes into the given entries' ``worked_count``.

        The first time an entry is seen, its current counts are captured as
        the pristine base; every apply then recomputes
        ``base + delta(log)``. Applying twice, or applying to a re-ingested
        copy of the same record, yields the same result — never a
        double-count.

        Args:
            entries: Indexed entries to adjust in place.

        Returns:
            How many entries were adjusted (had at least one outcome).
        """
        deltas = self.entry_deltas()
        adjusted = 0
        for entry in entries:
            if entry.id not in self._base_worked:
                self._base_worked[entry.id] = entry.worked_count
            if entry.id not in deltas:
                continue
            worked, attempted = self._base_worked[entry.id]
            d_worked, d_attempted = deltas[entry.id]
            entry.worked_count = (worked + d_worked, attempted + d_attempted)
            adjusted += 1
        return adjusted

    def __len__(self) -> int:
        """Number of confirmed outcomes in the log."""
        return len(self._records)

    def _load(self) -> None:
        if self.path is None or not self.path.exists():
            return
        with self.path.open(encoding="utf-8") as f:
            raw = json.load(f)
        if not isinstance(raw, list):
            raise ValueError(f"{self.path}: expected a JSON list of outcomes")
        self._records = [OutcomeRecord.from_dict(item) for item in raw]

    def _save(self) -> None:
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump([record.to_dict() for record in self._records], f, indent=2)
        tmp.replace(self.path)
