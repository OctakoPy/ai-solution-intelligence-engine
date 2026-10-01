"""Categories + sources analytics endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from apps.api.engine_cache import get_engine
from apps.api.models import CategoriesResponse, SourcesResponse

router = APIRouter(tags=["analytics"])


def _pretty_category(raw: str) -> str:
    """Map raw category id to a human-friendly display label."""
    overrides = {
        "account_access": "Access/Login",
        "email": "Email/Outlook",
        "network_vpn": "Network/VPN",
        "hr_systems": "HR Systems",
        "kb_maintenance": "KB Maintenance",
        "sap_addons": "SAP Add-ons",
        "sap_authorization": "SAP Authorization",
        "sap_batch_jobs": "SAP Batch Jobs",
        "sap_fiori": "SAP Fiori",
        "sap_interfaces": "SAP Interfaces",
        "sap_performance": "SAP Performance",
        "sap_workflow": "SAP Workflow",
        "sharepoint_access": "SharePoint Access",
    }
    return overrides.get(raw, raw.replace("_", " ").title())


@router.get("/api/categories", response_model=CategoriesResponse)
async def categories() -> CategoriesResponse:
    """Return unique categories present in the ingested dataset (pretty labels)."""
    engine = get_engine()
    cats = sorted({_pretty_category(e.category) for e in engine.index.entries})
    return CategoriesResponse(categories=cats)


@router.get("/api/sources", response_model=SourcesResponse)
async def sources() -> SourcesResponse:
    """Return counts per source type across the ingested dataset."""
    engine = get_engine()
    counts = {st: 0 for st in ("service_desk", "sap", "sharepoint", "knowledge_base")}
    for entry in engine.index.entries:
        if entry.source_type in counts:
            counts[entry.source_type] += 1
    return SourcesResponse(**counts)
