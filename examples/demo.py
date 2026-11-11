# -*- coding: utf-8 -*-
"""Five-scenario walkthrough for agent-route-grid (no network needed)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from routegrid import AgentSpec, Coordinator, ScopeGuard, Task
from routegrid.trail import AuditTrail

TEAM = [
    AgentSpec(name="worker", roles=("analyst",), capabilities=("lookup",),
              scope="ws-worker"),
    AgentSpec(name="reviewer", roles=("reviewer",), capabilities=("lookup",),
              scope="ws-reviewer", review_capable=True),
    AgentSpec(name="panel-a", capabilities=("lookup",), scope="ws-pa"),
    AgentSpec(name="panel-b", capabilities=("lookup",), scope="ws-pb"),
]


def job(task):
    return {"summary": "completed %s" % task.name, "value": 42}


def approve(task, ctx):
    return {"verdict": "approve", "note": "independent check passed"}


def main():
    trail = AuditTrail()
    co = Coordinator(TEAM, trail=trail, timeout_s=2.0)
    fns = {a.name: job for a in TEAM}
    revs = {"reviewer": approve}

    def run(label, task):
        res = co.route(task, worker_fns=fns, reviewer_fns=revs, self_exec=job)
        print("%s -> zone=%s strategy=%s fail_closed=%s calls=%s" % (
            label, res.zone, res.strategy, res.fail_closed,
            [(c.agent, c.status) for c in res.calls]))

    print("== zone routing ==")
    run("1 green  ", Task(name="routine lookup", risk="low", requires=("lookup",)))
    run("2 yellow ", Task(name="medium decision", risk="medium", requires=("lookup",)))
    run("3 red    ", Task(name="high-risk panel", risk="high", requires=("lookup",)))
    run("4 purple ", Task(name="training task", risk="low", opts=("training",),
                          requires=("lookup",)))

    print("\n== workspace isolation ==")
    guard = ScopeGuard(TEAM)
    print("worker -> own workspace  :",
          guard.can_write(TEAM[0], "ws-worker"))
    print("worker -> other workspace:",
          guard.can_write(TEAM[0], "ws-reviewer"))

    print("\n== trail verification ==")
    ok, bad, total = trail.verify()
    print("trail entries:", total, "| verify:", "OK" if ok else "TAMPERED at %s" % bad)

    print("\n== fail-closed demo: panicked worker ==")
    broken = dict(fns)
    broken["panel-a"] = lambda t: (_ for _ in ()).throw(RuntimeError("boom"))
    res = co.route(Task(name="risky panel", risk="high", requires=("lookup",)),
                   worker_fns=broken, reviewer_fns=revs, self_exec=job)
    print("zone=%s fail_closed=%s calls=%s" % (
        res.zone, res.fail_closed, [(c.agent, c.status) for c in res.calls]))


if __name__ == "__main__":
    main()