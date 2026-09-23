# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Trust-first "WHY THIS" evidence panel on Find a Solution and Chat:
  per-signal score breakdown, prior success (worked/attempted with %),
  supporting evidence records from other source systems, and deterministic
  caveats (#17, #25).
- "Knows when not to guess": one shared abstain policy governing Find,
  Chat, and the pilot evaluation; `next_best_action` on `/api/search` and
  `/api/chat` responses; amber guidance banner in the UI; context-trap
  "verify root cause" caveat on the why panel (#18, #26; ADR-003).
- Demo verification script: a replicable click-through flow with expected
  results for manual or audience verification of the trust behaviors
  (`docs/tutorials/verification-script.md`).

### Changed

- Chat now ranks through the same shared outcome-aware ranking path as
  Find a Solution, with deterministic tie-breaks (confidence, success rate,
  similarity, entry id); a repeatedly-failed fix can no longer outrank a
  proven one on any surface (#15, #24).
- Chat reply percentages are rounded consistently with the UI badges.

### Fixed

- `ConfidenceScorer` doctest expected value updated to match the current
  signal weights.

## [0.10.0] - 2026-07-18

- Initial public release of the Solution Intelligence Engine: multi-stage
  ingestion pipeline, trilingual semantic retrieval, outcome-aware
  confidence scoring, conversational agent, React dashboard.
