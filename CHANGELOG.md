# Changelog

## v0.1.0 (2026-11-11)

- Initial public release candidate.
- Zone policy: `policy.py` (green/yellow/red/purple mapping, panel selection).
- Coordinator: `coordinator.py` (self-execute / delegate+review / panel /
  mentor paths, per-call timeout, fail-closed worker handling, trail emit).
- Isolation: `scope.py` (workspace write guard).
- Trail: `trail.py` (append-only JSONL + sha256 hash chain, offline verify).
- Examples: `examples/demo.py` (five-scenario walkthrough).
- Tests: 35 unit tests covering policy, isolation, trail integrity, and
  fail-closed routing.