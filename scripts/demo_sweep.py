"""Run the demo query set through both engine surfaces and report behavior.

Requires a running API (``just api``).

    uv run python scripts/demo_sweep.py
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from typing import Any

BASE = "http://127.0.0.1:8004"

# (label, query, context) - one per category, plus the flows that matter.
QUERIES: list[tuple[str, str, dict[str, str] | None]] = [
    (
        "SAP auth clear",
        "a finance user cannot run SAP FI reports, getting S_RS_COMP authorization error",
        None,
    ),
    ("SAP auth vague", "finance user cannot open the report", None),
    (
        "SAP auth ctx",
        "finance user cannot open the report",
        {"error_code": "S_RS_COMP", "module": "SAP FICO", "environment": "PROD"},
    ),
    (
        "SAP MM posting",
        "goods receipt posting error in SAP MM, account determination issue",
        None,
    ),
    ("SAP MM perf", "sap transaction me23n running slow for finance team", None),
    (
        "SAP batch",
        "the nightly sap batch job for inventory reconciliation keeps short dumping",
        None,
    ),
    (
        "SAP Fiori tile",
        "po approval tile missing from fiori launchpad after update",
        None,
    ),
    (
        "SAP Fiori inbox",
        "my inbox fiori app is not showing approval items for the it operations manager",
        None,
    ),
    ("SAP workflow", "cannot open excel attachment from sap workflow inbox", None),
    ("SAP interfaces", "recurring idoc processing errors in logistics", None),
    ("SAP addon", "custom sap add-on causing session timeouts", None),
    ("VPN", "VPN drops after 5 minutes, reconnect fails on Windows 11", None),
    ("AD lockout", "user locked out of account after failed login attempts", None),
    ("AD vague", "cannot log in to my computer", None),
    ("Outlook sync", "Outlook not syncing new emails", None),
    ("Outlook send", "outlook cannot send email, stuck in outbox", None),
    ("SharePoint", "cannot access project SharePoint site", None),
    ("SharePoint vague", "cannot get into the site", None),
    ("Printer", "printer on 3rd floor not responding", None),
    ("Licensing", "need additional SAP GUI license for new consultant", None),
    ("Onboarding", "new employee laptop setup standard procedure", None),
    ("KB maintenance", "KB article outdated for ZREPORT01 process", None),
    ("OFFTOPIC milk", "i ran out of milk in my house", None),
    ("OFFTOPIC weather", "what is the weather in london tomorrow", None),
    ("OFFTOPIC lunch", "where is a good place to get lunch near here", None),
    ("OFFTOPIC gym", "how do i book a dentist appointment", None),
]

# Records the ingestion pipeline deliberately keeps out of the index, so these
# have nothing to retrieve and are not demo queries:
#   compliance  -> quality_flag "junk"      (auto-rejected)
#   hr_systems  -> access_level "restricted" (security filter)
#   sap_addons  -> status "Escalated"       (unresolved, no proven fix)

# Labels that get a follow-up turn, and the follow-up to send.
FOLLOW_UPS: dict[str, str] = {
    "SAP MM perf": "that did not work, same problem still happening",
    "SAP auth vague": "error code S_RS_COMP, module SAP FICO, environment PROD",
    "Outlook send": "that did not work, still stuck in outbox",
    "SharePoint vague": "error code ACCESS_DENIED, module SharePoint, environment PROD",
    "AD vague": "that did not work, still cannot log in",
}


def post(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as exc:
        return {"_error": exc.code, "_body": exc.read().decode()[:300]}
    except urllib.error.URLError as exc:
        return {"_error": "conn", "_body": str(exc)}


def describe(label: str, body: dict[str, Any]) -> tuple[str, str | None, dict | None]:
    """Return (summary line, verdict action, top result) for one response."""
    if "_error" in body:
        return f"{label:20} HTTP {body['_error']}: {body['_body']}", None, None
    nba = body.get("next_best_action")
    action = "PROCEED" if not nba else nba["action"]
    results = body.get("results") or body.get("candidates") or []
    if not results:
        return f"{label:20} {action:12} -- no results --", action, None
    top = results[0]
    summary = (
        f"{label:20} {action:12} {top['id']:9} {str(top.get('category')):19} "
        f"{top['confidence']:.3f} w{top.get('worked')}/{top.get('attempted'):<3} "
        f"| {top['title'][:46]}"
    )
    return summary, action, top


def run_online() -> int:
    problems = 0
    print("=" * 118)
    print("FIND A SOLUTION - POST /api/search")
    print("=" * 118)
    find: dict[str, tuple[str | None, dict | None]] = {}
    for label, query, ctx in QUERIES:
        body = post("/api/search", {"query": query, "context": ctx})
        line, action, top = describe(label, body)
        print(line)
        find[label] = (action, top)

    print()
    print("=" * 118)
    print("CHAT - POST /api/chat/start")
    print("=" * 118)
    chat: dict[str, tuple[str | None, dict | None]] = {}
    for idx, (label, query, ctx) in enumerate(QUERIES):
        body = post(
            "/api/chat/start",
            {"query": query, "session_id": f"sweep{idx}", "context": ctx},
        )
        line, action, top = describe(label, body)
        print(line)
        chat[label] = (action, top)

    print()
    print("=" * 118)
    print("CHAT FOLLOW-UPS - POST /api/chat/respond")
    print("=" * 118)
    for idx, (label, query, _) in enumerate(QUERIES):
        if label not in FOLLOW_UPS:
            continue
        body = post(
            "/api/chat/respond",
            {"session_id": f"sweep{idx}", "message": FOLLOW_UPS[label]},
        )
        if "_error" in body:
            print(f"{label:20} HTTP {body['_error']}: {body['_body']}")
            problems += 1
            continue
        line, action, top = describe(label, body)
        print(line)
        print(f"{'':20} -> {body['turns'][-1]['text'][:160]}")
        print()

    print("=" * 118)
    print("CROSS-SURFACE CHECK - same query must give the same record")
    print("=" * 118)
    for label, _, _ in QUERIES:
        fa, ft = find[label]
        ca, ct = chat[label]
        fid = ft["id"] if ft else "-"
        cid = ct["id"] if ct else "-"
        same = fid == cid
        # Chat boosts its displayed score, so only the record must agree.
        flag = "" if same else "  <-- MISMATCH"
        if not same:
            problems += 1
        print(f"{label:20} find={fid:9} chat={cid:9}{flag}")

    print()
    print("=" * 118)
    print("SANITY CHECKS")
    print("=" * 118)
    for label, _, _ in QUERIES:
        off = label.startswith("OFFTOPIC")
        action = find[label][0]
        if off and action == "PROCEED":
            print(f"{label:20} PROCEED - should have declined{'':<4}")
            problems += 1
        elif not off and action is None:
            print(f"{label:20} error response")
            problems += 1
    print(f"problems: {problems}")
    return problems


def main() -> int:
    return run_online()


if __name__ == "__main__":
    sys.exit(0 if main() == 0 else 1)
