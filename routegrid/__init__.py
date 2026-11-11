# -*- coding: utf-8 -*-
"""agent-route-grid (routegrid): an audited routing layer for multi-agent teams.

The library makes explicit what most agent frameworks leave implicit:
  - WHO may execute a task (zone-based routing policy)
  - WHO may review or join a panel (independent verification)
  - WHAT was delegated / decided / returned (append-only, hash-chained trail)

Every route decision is recorded and verifiable. Fail-closed: a worker error
or timeout never produces an "allow"-shaped success result.

Research prototype / AI-assisted development. MIT licensed.
"""

from .coordinator import Coordinator, RouteResult
from .models import AgentSpec, Task
from .policy import ZonePolicy, ZONES
from .scope import ScopeGuard
from .trail import AuditTrail

__all__ = [
    "AgentSpec",
    "Task",
    "ZonePolicy",
    "ZONES",
    "ScopeGuard",
    "AuditTrail",
    "Coordinator",
    "RouteResult",
]

__version__ = "0.1.0"