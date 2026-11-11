# agent-route-grid

An **audited routing layer** for multi-agent teams. It makes explicit what most
agent frameworks leave implicit: *who* may execute a task (zone-based routing),
*who* may review or join a panel (independent verification), and *what* was
delegated, decided, and returned (hash-chained trail).

*Research prototype / AI-assisted development. MIT licensed.*

## Why

Multi-agent teams grow fast and drift into chaos: nobody knows who was supposed
to decide, whether anyone reviewed it, or what happened. This library turns
routing into a **visible policy** and every decision into a **verifiable
record** — the same fail-closed philosophy as the
[agent-call-audit](https://gitcode.com/gcw_MKhSyoGN/agent-call-audit) family.

## Route zones

| Zone | When | Strategy |
|:--|:--|:--|
| green | low risk, routine | coordinator self-executes |
| yellow | medium risk | delegate to one capable worker, then independent review |
| red | high / critical risk | panel consultation, aggregate; any fault keeps result fail-closed |
| purple | training / mentorship | route as a learning exercise with a referee |

## Install

```bash
pip install agent-route-grid   # once published
# dev / from source:
pip install -e .
```

Zero runtime dependencies. Python 3.9+.

## Quick start

```python
from routegrid import AgentSpec, Coordinator, Task

team = [
    AgentSpec(name="worker", capabilities=("lookup",), scope="ws-w"),
    AgentSpec(name="reviewer", capabilities=("lookup",), scope="ws-r",
              review_capable=True),
]

co = Coordinator(team, timeout_s=2.0)
res = co.route(
    Task(name="medium decision", risk="medium", requires=("lookup",)),
    worker_fns={"worker": lambda t: {"summary": "done"}},          # injected executors
    reviewer_fns={"reviewer": lambda t, ctx: {"verdict": "approve"}},
)
print(res.zone, res.strategy, res.fail_closed)   # yellow delegate+review False
```

Run the five-scenario walkthrough:

```bash
python examples/demo.py
```

## Workspace isolation

Agents may only write their own `scope` (plus declared `shared` workspaces).
Attempts to write anything else are denied:

```python
from routegrid import ScopeGuard
guard = ScopeGuard(team)
guard.assert_write(team[0], "ws-w")          # ok
guard.assert_write(team[0], "ws-r")          # PermissionError
```

## Verifiable trail

Every `route()` appends a hash-chained event (`task`, `zone`, `strategy`,
per-call statuses, `fail_closed`). Check the whole chain anytime:

```python
co.trail.verify()   # (ok, first_bad_index_or_None, total)
```

## Fail-closed invariants

| Invariant | Guarantee |
|:--|:--|
| Worker fault -> fail_closed | a worker error/timeout marks the call and the route result fail-closed |
| Reviewer fault -> fail_closed | an unavailable/broken review keeps the result fail-closed |
| Panel dissent | red-zone panel with any non-ok call keeps denial semantics |
| Scope isolation | writing another agent's workspace is denied |
| Trail tamper-evident | `verify()` detects any modification to the chain |

## Architecture

```
routegrid/
├── models.py       AgentSpec / Task / WorkerCall / RouteResult
├── policy.py       ZonePolicy (zone_for / panel_members), DEFAULT_POLICY
├── coordinator.py  Coordinator: route() by zone, timestamped threads, trail
├── scope.py        ScopeGuard: workspace write isolation
└── trail.py        AuditTrail: append-only JSONL + sha256 chain
examples/           demo.py (five-scenario walkthrough)
tests/              35 unit tests
```

## Contributing / Security

- [CONTRIBUTING.md](CONTRIBUTING.md) — fail-closed first, sanitized commits,
  green tests.
- [SECURITY.md](SECURITY.md) — report privately; reference implementation.

## License

MIT — see [LICENSE](LICENSE). Maintainers: `agent-route-grid maintainers`.