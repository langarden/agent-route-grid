# agent-route-grid

> **An audited routing layer for multi-agent teams** — zone-based routing policy,
> workspace isolation, and a hash-chained decision trail. Who executes, who
> reviews, who decides — visible and verifiable.

```bash
pip install agent-route-grid            # zero deps, Python 3.9+
```

![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![Tests](https://img.shields.io/badge/tests-35%20passed-green)
![Deps](https://img.shields.io/badge/runtime%20deps-0-green)
![Status](https://img.shields.io/badge/status-research%20prototype-orange)

<a href="https://gitcode.com/gcw_MKhSyoGN/agent-route-grid"><img src="https://img.shields.io/badge/GitCode-gcw_MKhSyoGN%2Fagent-route-grid-blue" alt="GitCode"></a>
<a href="https://github.com/langarden/agent-route-grid"><img src="https://img.shields.io/badge/GitHub-langarden%2Fagent-route-grid-black" alt="GitHub"></a>

[中文版](docs/README.zh-CN.md) · *Research prototype / AI-assisted development.*

---

Multi-agent teams grow fast and drift into chaos: nobody knows who was supposed
to decide, whether anyone reviewed it, or what actually happened. This library
turns routing into a **visible policy** and every decision into a **verifiable
record**.

## Why a routing layer?

Most agent frameworks hand you workers; nobody hands you **governance**. This
library packages the governance questions a real team asks:

- **Who may execute this?** → zone policy (risk-based)
- **Who reviews it?** → independent reviewer (yellow zone)
- **Who else needs a say?** → panel consultation (red zone)
- **What happened?** → hash-chained trail, `verify()` offline

## Route zones

| Zone | When | Strategy |
|:--|:--|:--|
| `green` | low risk, routine | coordinator self-executes |
| `yellow` | medium risk | delegate to one worker, then **independent review** |
| `red` | high / critical risk | **panel consultation**, aggregate; any fault keeps fail-closed |
| `purple` | training / mentorship | route as a learning exercise with a referee |

The mapping is deterministic and injectable: pass your own `ZonePolicy`.

## Product family

Part of the **Verifiable-agent family** — one fail-closed design language:

| Repo | Role |
|:--|:--|
| [agent-call-audit](https://gitcode.com/gcw_MKhSyoGN/agent-call-audit) | audit **engine** for agent tool calls |
| [agent-memory-ledger](https://gitcode.com/gcw_MKhSyoGN/agent-memory-ledger) | verifiable **memory** layer |
| [agent-audit-gateway](https://gitcode.com/gcw_MKhSyoGN/agent-audit-gateway) | HTTP **gateway** around the engine |
| **agent-route-grid** | audited multi-agent **routing** (this repo) |

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
    worker_fns={"worker": lambda t: {"summary": "done"}},          # your executors
    reviewer_fns={"reviewer": lambda t, ctx: {"verdict": "approve"}},
)
print(res.zone, res.strategy, res.fail_closed)   # yellow delegate+review False
```

Workers are **injected callables** — the coordinator never runs business logic;
it only routes, times out, collects, and records.

## Proof of life

Real output from `python examples/demo.py`:

```
1 green  -> zone=green  strategy=self-execute   fail_closed=False
2 yellow -> zone=yellow strategy=delegate+review fail_closed=False
3 red    -> zone=red    strategy=panel+aggregate fail_closed=False
4 purple -> zone=purple strategy=mentor          fail_closed=False
workspace isolation: worker->own True | worker->other False
trail verification: 4 entries, OK
fail-closed demo: panel-a errored -> fail_closed=True
```

## Fail-closed invariants

| Invariant | Guarantee |
|:--|:--|
| Worker fault | worker error/timeout marks the call and route result fail-closed |
| Reviewer fault | missing/broken review keeps the result fail-closed |
| Panel dissent | red-zone panel with any non-ok call keeps denial semantics |
| Scope isolation | writing another agent's workspace is denied |
| Trail tamper-evident | `verify()` detects any modification to the chain |

## Architecture

```
routegrid/
├── models.py       AgentSpec / Task / WorkerCall / RouteResult
├── policy.py       ZonePolicy (zone_for / panel_members), DEFAULT_POLICY
├── coordinator.py  Coordinator: route() by zone, timed threads, trail
├── scope.py        ScopeGuard: workspace write isolation
└── trail.py        AuditTrail: append-only JSONL + sha256 chain
examples/           demo.py (five-scenario walkthrough)
tests/              35 unit tests
```

## Roadmap ideas

- Async orchestration (parallel panel with fan-out)
- Plugin hooks for human-in-the-loop review UIs
- Trail exporter (MCP / OTel)

## Contributing / Security / License

- [CONTRIBUTING.md](CONTRIBUTING.md) — fail-closed first, sanitized commits,
  green tests.
- [SECURITY.md](SECURITY.md) — report privately; reference implementation.
- [LICENSE](LICENSE) — MIT, `agent-route-grid maintainers`.