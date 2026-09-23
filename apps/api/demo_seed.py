"""Deterministic Resolution Memory seed for the live demo.

The Overview dashboard's Resolution Memory panel must be populated from the
first frame of every demo run, so the API process resets the outcome log to
this fixed seed the first time the shared memory is built (wired in
``apps.api.engine_cache._shared_memory``): every restart starts from the
same known learning state, and live outcomes recorded during the session
apply on top until the next restart.

Every entry id here was chosen to avoid each record the demo script quotes
(``TIC-1001`` must stay 8/8 for the voiceover, and the VPN / auth /
multilingual / chat stars and the ``M8149`` context pair must keep their
scripted rankings and track records), so seeding never disturbs a scripted
beat. Timestamps are computed relative to seed time — oldest first, newest
recorded roughly half an hour ago — so the dashboard's "last outcome"
recency line is always fresh at boot.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from solution_intelligence.memory import ResolutionMemory

# (entry_id, worked, hours_ago, note) — one outcome per knowledge record.
# Hours ago are relative to seed time; ``seed_memory`` records oldest first.
SEED_OUTCOMES: tuple[tuple[str, bool, float, str], ...] = (
    ("TIC-1026", True, 96.0, "License seats refreshed, app launches again."),
    ("TIC-1017", True, 74.0, "OST rebuild restored Outlook sync."),
    ("TIC-1028", False, 60.0, "Still waiting on site-owner approval."),
    ("TIC-1021", True, 52.0, "Cleared paper jam, test page printed."),
    ("TIC-1041", True, 44.0, "SAP note applied, ME23N loads normally."),
    ("TIC-1020", False, 38.0, "Delegation missing after mailbox move."),
    ("TIC-1024", True, 31.0, "Dock firmware update restored displays."),
    ("TIC-1053", True, 26.0, "Inheritance re-enabled on the Sales library."),
    ("TIC-1029", True, 19.0, "Files restored from version history."),
    ("SAP-1044", False, 14.0, "Partner profile still misconfigured."),
    ("TIC-1018", True, 9.0, "Queue cleared after transport restart."),
    ("KB_-1058", True, 6.0, "Graphics filter disabled, attachments open."),
    ("TIC-1043", True, 3.0, "FBL3N role assigned via SU01."),
    ("TIC-1016", True, 0.5, "Temp password set, user signed in."),
)

SEED_SOURCE = "ui"


def seed_memory(memory: ResolutionMemory) -> int:
    """Reset ``memory`` to the fixed demo seed.

    Clears any outcomes loaded from a previous session, then records the
    seed table oldest-first so the newest record is always last (the
    dashboard reads recency from the last record).

    Args:
        memory: The Resolution Memory to reset and seed.

    Returns:
        How many outcomes were written.
    """
    memory.clear()
    now = datetime.now(timezone.utc)
    for entry_id, success, hours_ago, note in sorted(
        SEED_OUTCOMES, key=lambda row: -row[2]
    ):
        memory.record(
            entry_id,
            success,
            note=note,
            source=SEED_SOURCE,
            timestamp=(now - timedelta(hours=hours_ago)).isoformat(timespec="seconds"),
        )
    return len(SEED_OUTCOMES)
