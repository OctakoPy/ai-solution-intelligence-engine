"""Solution Intelligence Engine — AI-powered enterprise knowledge intelligence.

Unifies ticketing, SAP, SharePoint and knowledge base systems into one
searchable index, surfaces proven solutions for new support issues, and
drives a trust-first "why" panel for non-technical audiences.
"""

from solution_intelligence.service import SolutionEngine
from solution_intelligence.sources import (
    KnowledgeBaseConnector,
    SapConnector,
    SharePointConnector,
    TicketConnector,
    load_entries,
    load_filtered,
)

__all__ = [
    "SolutionEngine",
    "KnowledgeBaseConnector",
    "SapConnector",
    "SharePointConnector",
    "TicketConnector",
    "load_entries",
    "load_filtered",
]
