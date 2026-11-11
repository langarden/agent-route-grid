# Security

## Reporting a vulnerability

Please report vulnerabilities privately to the maintainers at
`2307788504@qq.com`. Do not open a public issue for security problems.

## Design posture

**Fail-closed.** The coordinator assumes the worst about workers:

- worker error / timeout -> call marked fail-closed; route result fail-closed
- reviewer missing / broken -> route result fail-closed
- red-zone panel with any non-ok call -> fail-closed aggregate
- workspace write outside a scope -> PermissionError
- trail entry modified -> `verify()` returns False

## Status

**Research prototype / reference implementation**, not a hardened production
product. Review the code before relying on it in production.

## Responsible disclosure

- Do not test on third-party systems.
- Do not include real secrets or credentials in any issue or commit.
- Include a minimal repro (code + commands) when possible.