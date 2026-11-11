# Contributing

Thanks for considering contributing to agent-route-grid.

## Guiding principles

1. **Fail-closed first.** A worker/reviewer fault must never surface as a
   successful route result.
2. **No new dependencies.** The project is zero-runtime-dependency by design.
3. **Sanitized commits.** No secrets, no personal/organization identifiers,
   no machine paths.
4. **Tests stay green.** Every change must keep the suite passing.

## Quick start

```bash
pip install -e .
python -m unittest discover -s tests -t . -v
python examples/demo.py
```

## Pull requests

- One logical change per PR.
- Add tests for new behavior; regression tests for bug fixes.
- Reference the invariant (README table) your change relates to.

## Extending the policy

`ZonePolicy.zone_for(task)` is deterministic and injectable: pass your own
policy to `Coordinator(policy=...)` instead of subclassing.