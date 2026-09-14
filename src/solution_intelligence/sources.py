"""Mock connectors that simulate the four enterprise source systems.

Each connector exposes a small, consistent API so the ingestion pipeline
does not care whether a record came from a ticket system, SAP, SharePoint,
or the knowledge base. In a real deployment each connector would wrap a live
API; for the demo they simply read from the bundled synthetic dataset.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from solution_intelligence.models import KnowledgeEntry

DEFAULT_DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "knowledge.json"


class SourceConnector:
    """Base class for a source-system connector."""

    source_type: str = "unknown"

    def fetch(self, entries: Iterable[KnowledgeEntry]) -> list[KnowledgeEntry]:
        """Return the knowledge entries for this source."""
        raise NotImplementedError


class TicketConnector(SourceConnector):
    """Simulates the enterprise ticketing system."""

    source_type = "ticket"

    def fetch(self, entries: Iterable[KnowledgeEntry]) -> list[KnowledgeEntry]:
        return [e for e in entries if e.source_type == "ticket"]


class SapConnector(SourceConnector):
    """Simulates the SAP system (notes and transactions)."""

    source_type = "sap_note"

    def fetch(self, entries: Iterable[KnowledgeEntry]) -> list[KnowledgeEntry]:
        return [e for e in entries if e.source_type == "sap_note"]


class SharePointConnector(SourceConnector):
    """Simulates SharePoint document libraries."""

    source_type = "sharepoint_doc"

    def fetch(self, entries: Iterable[KnowledgeEntry]) -> list[KnowledgeEntry]:
        return [e for e in entries if e.source_type == "sharepoint_doc"]


class KnowledgeBaseConnector(SourceConnector):
    """Simulates the knowledge base system."""

    source_type = "kb_article"

    def fetch(self, entries: Iterable[KnowledgeEntry]) -> list[KnowledgeEntry]:
        return [e for e in entries if e.source_type == "kb_article"]


def load_entries(path: str | Path | None = None) -> list[KnowledgeEntry]:
    """Load all knowledge entries from the synthetic dataset file."""
    data_path = Path(path) if path else DEFAULT_DATA_PATH
    with data_path.open(encoding="utf-8") as f:
        raw_items = json.load(f)
    return [KnowledgeEntry.from_dict(item) for item in raw_items]


def load_filtered(
    path: str | Path | None = None,
    *,
    max_total: int | None = None,
) -> list[KnowledgeEntry]:
    """Load entries, optionally trimming to a small demo subset.

    When ``max_total`` is set and less than total available, returns a
    balanced slice across all four source types so the demo shows every
    source feeding in. When ``max_total`` >= total available, returns all.
    """
    entries = load_entries(path)
    if max_total is None or max_total <= 0 or max_total >= len(entries):
        return entries

    connectors = [
        TicketConnector,
        SapConnector,
        SharePointConnector,
        KnowledgeBaseConnector,
    ]
    selected: list[KnowledgeEntry] = []
    per_source = max(1, max_total // len(connectors))
    for connector_cls in connectors:
        connector = connector_cls()
        subset = connector.fetch(entries)
        selected.extend(subset[:per_source])
    return selected[:max_total]
