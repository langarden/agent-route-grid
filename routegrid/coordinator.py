# -*- coding: utf-8 -*-
"""Coordinator: decides WHO, records WHAT (trail), keeps results fail-closed.

Workers are injected as callables: ``worker_fns[agent_name](task) -> dict``.
The coordinator never executes business logic itself — it only routes,
times out, collects, and records. A worker error/timeout marks the call
fail-closed; a red-zone panel with any dissent keeps denial semantics.
"""
from __future__ import annotations

import threading
import time
from typing import Callable, Dict, Optional

from .models import AgentSpec, RouteResult, Task, WorkerCall
from .policy import DEFAULT_POLICY, ZonePolicy
from .scope import ScopeGuard
from .trail import AuditTrail

WorkerFn = Callable[[Task], dict]
ReviewFn = Callable[[Task, dict], dict]


class Coordinator:
    """Routes tasks by zone policy, records everything in a hash-chained trail."""

    def __init__(
        self,
        agents,
        trail: Optional[AuditTrail] = None,
        policy: Optional[ZonePolicy] = None,
        timeout_s: float = 10.0,
    ):
        self.agents = {a.name: a for a in agents}
        self.policy = policy or DEFAULT_POLICY
        self.trail = trail or AuditTrail()
        self.scope = ScopeGuard(agents)
        self.timeout_s = timeout_s
        self._lock = threading.Lock()

    # ------------------------------------------------------------------ API
    def route(
        self,
        task: Task,
        worker_fns: Optional[Dict[str, WorkerFn]] = None,
        reviewer_fns: Optional[Dict[str, ReviewFn]] = None,
        self_exec: Optional[WorkerFn] = None,
    ) -> RouteResult:
        """Route one task. Returns a RouteResult; never raises for worker faults."""
        zone = self.policy.zone_for(task)
        workers = worker_fns or {}
        reviewers = reviewer_fns or {}
        description = self.policy.describe(task)

        if zone == "green":
            return self._green(task, self_exec, workers)
        if zone == "yellow":
            return self._yellow(task, workers, reviewers)
        if zone == "red":
            return self._red(task, workers)
        if zone == "purple":
            return self._purple(task, workers, reviewers)
        raise ValueError("unknown zone: %s" % zone)  # unreachable

    # ------------------------------------------------------------ zone paths
    def _green(self, task, self_exec, workers) -> RouteResult:
        calls, status, summary = self._invoke("coordinator", self_exec, task, workers)
        fail_closed = status != "ok"
        return self._emit(task, "green", "self-execute", calls, fail_closed,
                          result=summary if fail_closed else None)

    def _yellow(self, task, workers, reviewers) -> RouteResult:
        calls, fail_closed, result = self._delegate_review(task, workers, reviewers)
        return self._emit(task, "yellow", "delegate+review", calls, fail_closed, result)

    def _purple(self, task, workers, reviewers) -> RouteResult:
        calls, fail_closed, result = self._delegate_review(task, workers, reviewers)
        return self._emit(task, "purple", "mentor", calls, fail_closed, result)

    def _delegate_review(self, task, workers, reviewers):
        """Shared delegate + independent-review path (yellow & purple)."""
        picks = [a.name for a in self._capable(task)]
        if not picks:
            return ([WorkerCall("none", "error", 0.0, "no capable worker",
                                fail_closed=True)],
                    True, {"reason": "no capable worker"})
        worker_name = picks[0]
        calls, status, summary = self._invoke(worker_name, workers.get(worker_name),
                                              task, workers)
        if status != "ok":
            return calls, True, {"reason": summary}
        reviewer = self._pick_reviewer(task, worker_name, reviewers)
        if reviewer is None:
            return calls, True, {"reason": "no independent reviewer available"}
        rev_start = time.monotonic()
        try:
            rev = reviewers[reviewer](task, {"worker": worker_name, "result": summary})
            reviewer_status = "ok"
            rev_summary = str(rev.get("verdict", rev))
            rev_latency = (time.monotonic() - rev_start) * 1000
        except Exception as exc:  # noqa: BLE001 - fail-closed
            reviewer_status = "error"
            rev_summary = "reviewer error: %s" % type(exc).__name__
            rev_latency = (time.monotonic() - rev_start) * 1000
        calls.append(WorkerCall(reviewer, reviewer_status, round(rev_latency, 2),
                                "review: " + rev_summary[:120],
                                fail_closed=reviewer_status != "ok"))
        if reviewer_status != "ok":
            return calls, True, {"reason": rev_summary}
        return calls, False, {"worker": worker_name, "reviewer": reviewer,
                              "verdict": rev_summary}

    def _red(self, task, workers) -> RouteResult:
        picks = self.policy.panel_members(task, [a.name for a in self._capable(task)])
        if not picks:
            return self._emit(task, "red", "panel+aggregate",
                              [WorkerCall("none", "error", 0.0,
                                          "no panel member", fail_closed=True)],
                              fail_closed=True, result={"reason": "no panel member"})
        calls = []
        statuses = []
        for name in picks:
            worker_calls, status, _ = self._invoke(name, workers.get(name), task, workers)
            calls.extend(worker_calls)
            statuses.append(status)
        ok = all(s == "ok" for s in statuses)
        return self._emit(task, "red", "panel+aggregate", calls,
                          fail_closed=not ok,
                          result={"panel": list(picks), "statuses": statuses})

    # ---------------------------------------------------------------- helpers
    def _capable(self, task):
        if not task.requires:
            return [a for a in self.agents.values()]
        return [a for a in self.agents.values() if any(a.can(c) for c in task.requires)]

    def _pick_reviewer(self, task, worker_name, reviewers):
        for name in reviewers:
            if name != worker_name and name in self.agents and self.agents[name].review_capable:
                return name
        return None

    def _invoke(self, name, fn, task, workers) -> (list, str, str):
        calls = []
        if fn is None:
            return ([WorkerCall(name, "error", 0.0, "no executor fn", fail_closed=True)],
                    "error", "no executor fn")
        box = {}
        start = time.monotonic()

        def run():
            try:
                box["value"] = fn(task)
            except Exception as exc:  # noqa: BLE001
                box["error"] = exc

        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        thread.join(timeout=self.timeout_s)
        latency = (time.monotonic() - start) * 1000
        if thread.is_alive():
            calls.append(WorkerCall(name, "timeout", round(latency, 2),
                                    "worker exceeded %.1fs" % self.timeout_s,
                                    fail_closed=True))
            return calls, "timeout", "timeout after %.1fs" % self.timeout_s
        if "error" in box:
            calls.append(WorkerCall(name, "error", round(latency, 2),
                                    "error: %s" % type(box["error"]).__name__,
                                    fail_closed=True))
            return calls, "error", "worker error: %s" % type(box["error"]).__name__
        value = box.get("value") or {}
        calls.append(WorkerCall(name, "ok", round(latency, 2),
                                str(value.get("summary", value))[:120]))
        return calls, "ok", value

    def _emit(self, task, zone, strategy, calls, fail_closed, result=None):
        entry = {
            "event": "route",
            "task": task.name,
            "zone": zone,
            "strategy": strategy,
            "risk": task.risk,
            "calls": [c.__dict__ for c in calls],
            "fail_closed": fail_closed,
        }
        self.trail.append(entry)
        return RouteResult(
            task_name=task.name,
            zone=zone,
            strategy=strategy,
            calls=calls,
            result=result,
            fail_closed=fail_closed,
            trail_total=len(self.trail.entries),
        )