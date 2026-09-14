# Fix: Wrong check emojis in live animation

## Problem
In the live ingestion animation, TIC-1001 shows ❌ for all three checks (stage1, judge, duplicate) when using Debug (3) or Full (70) modes, but works correctly in Small (8) mode. The final verdict correctly shows "Added to Knowledge Index".

## Root Cause
In `_live_view_checks()`, the code uses:
```python
by_stage = {step.stage: step for step in checks}
idx = list(by_stage).index(stage)
```

This relies on dict insertion order from the `checks` list. But columns are fixed as `stage1`/`judge`/`duplicate`. When the `checks` list has a different order (e.g., `judge` before `stage1` in Debug/Full modes for TIC-1001), the index lookup returns wrong values, causing wrong emojis.

## Fix
Replace the index lookup with explicit order:
```python
CHECK_ORDER = ["stage1", "judge", "duplicate"]
idx = CHECK_ORDER.index(stage)
```

This ensures consistent column mapping regardless of `checks` list order.

## Files to modify
- `src/solution_intelligence/app.py` - `_live_view_checks()` function

## Test plan
Test all three modes (Debug 3, Small 8, Full 70) and verify TIC-1001 shows ✅ for all three checks in the live animation.
