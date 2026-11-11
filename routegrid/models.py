# -*- coding: utf-8 -*-
"""Core data models: agents, tasks, and route results."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List

RISK_LEVELS = ("low", "medium", "high", "critical")
TASK_OPTS = ("training", "mentor", "batch", "urgent")


@dataclass
class AgentSpec:
    """A worker agent in the team. Scope isolates its private workspace."""

    name: str
    roles: tuple = ()
    capabilities: tuple = ()
    scope: str = ""                  # private workspace id; writing it = owner only
    shared: tuple = ()               # workspaces this agent may also write
    review_capable: bool = False     # can act as an independent reviewer

    def can(self, capability: str) -> bool:
        return capability in self.capabilities

    def has_role(self, role: str) -> bool:
        return role in self.roles


@dataclass
class Task:
    """A unit of work to route. ``risk`` and ``opts`` drive the zone policy."""

    name: str
    payload: Any = None
    risk: str = "low"                  # low | medium | high | critical
    requires: tuple = ()               # capability requirements
    opts: tuple = ()                   # training | mentor | batch | urgent
    deadline_s: float = 60.0
    meta: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.risk not in RISK_LEVELS:
            raise ValueError("unknown risk: %s" % self.risk)
        for opt in self.opts:
            if opt not in TASK_OPTS:
                raise ValueError("unknown opt: %s" % opt)

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class WorkerCall:
    """One worker invocation recorded in the trail."""

    agent: str
    status: str = "ok"                 # ok | error | timeout
    latency_ms: float = 0.0
    summary: str = ""
    fail_closed: bool = False


@dataclass
class RouteResult:
    """Outcome of one route() invocation."""

    task_name: str
    zone: str
    strategy: str                      # self-execute | delegate+review | panel | mentor
    calls: List[WorkerCall] = field(default_factory=list)
    result: Any = None
    fail_closed: bool = False
    trail_total: int = 0

    def as_dict(self) -> dict:
        return asdict(self)