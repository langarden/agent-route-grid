# -*- coding: utf-8 -*-
import time
import unittest

from routegrid import AgentSpec, Coordinator, Task
from routegrid.trail import AuditTrail

WORKERS = [AgentSpec(name="worker", capabilities=("lookup",), scope="ws-w"),
           AgentSpec(name="reviewer", capabilities=("lookup",), scope="ws-r",
                     review_capable=True),
           AgentSpec(name="panel2", capabilities=("lookup",), scope="ws-p2"),
           AgentSpec(name="panel3", capabilities=("lookup",), scope="ws-p3")]


def ok_fn(task):
    return {"summary": "done %s" % task.name, "value": 1}


class CoordinatorTests(unittest.TestCase):
    def setUp(self):
        self.trail = AuditTrail()
        self.co = Coordinator(WORKERS, trail=self.trail, timeout_s=2.0)

    def test_green_self_execute(self):
        res = self.co.route(Task(name="t", risk="low", requires=("lookup",)),
                            worker_fns={w.name: ok_fn for w in WORKERS},
                            self_exec=ok_fn)
        self.assertEqual(res.zone, "green")
        self.assertEqual(res.strategy, "self-execute")
        self.assertFalse(res.fail_closed)
        self.assertEqual(res.calls[0].agent, "coordinator")

    def test_yellow_delegate_and_review(self):
        res = self.co.route(Task(name="t", risk="medium", requires=("lookup",)),
                            worker_fns={w.name: ok_fn for w in WORKERS},
                            reviewer_fns={"reviewer": lambda t, ctx: {"verdict": "approve"}})
        self.assertEqual(res.zone, "yellow")
        self.assertEqual(res.strategy, "delegate+review")
        self.assertFalse(res.fail_closed)
        self.assertEqual(res.calls[-1].agent, "reviewer")

    def test_yellow_no_reviewer_fail_closed(self):
        res = self.co.route(Task(name="t", risk="medium", requires=("lookup",)),
                            worker_fns={w.name: ok_fn for w in WORKERS},
                            reviewer_fns={})
        self.assertTrue(res.fail_closed)

    def test_red_panel_aggregate(self):
        res = self.co.route(Task(name="t", risk="high", requires=("lookup",)),
                            worker_fns={w.name: ok_fn for w in WORKERS})
        self.assertEqual(res.zone, "red")
        self.assertEqual(res.strategy, "panel+aggregate")
        self.assertFalse(res.fail_closed)
        self.assertGreaterEqual(len(res.calls), 3)

    def test_red_one_broken_fail_closed(self):
        fns = {w.name: ok_fn for w in WORKERS}
        fns["panel2"] = lambda t: (_ for _ in ()).throw(RuntimeError("boom"))
        res = self.co.route(Task(name="t", risk="high", requires=("lookup",)),
                            worker_fns=fns)
        self.assertTrue(res.fail_closed)

    def test_worker_timeout_fail_closed(self):
        co = Coordinator(WORKERS, trail=AuditTrail(), timeout_s=0.1)
        fns = {w.name: ok_fn for w in WORKERS}
        fns["worker"] = lambda t: time.sleep(0.5)
        res = co.route(Task(name="t", risk="medium", requires=("lookup",)),
                       worker_fns=fns, reviewer_fns={})
        self.assertTrue(res.fail_closed)

    def test_worker_error_fail_closed(self):
        fns = {w.name: ok_fn for w in WORKERS}
        fns["worker"] = lambda t: (_ for _ in ()).throw(ValueError("x"))
        res = self.co.route(Task(name="t", risk="medium", requires=("lookup",)),
                            worker_fns=fns, reviewer_fns={})
        self.assertTrue(res.fail_closed)

    def test_no_capable_worker_fail_closed(self):
        res = self.co.route(Task(name="t", risk="medium", requires=("nonexistent",)),
                            worker_fns={}, reviewer_fns={})
        self.assertTrue(res.fail_closed)
        self.assertEqual(res.calls[0].agent, "none")

    def test_purple_mentor(self):
        res = self.co.route(Task(name="t", risk="low", opts=("training",),
                                 requires=("lookup",)),
                            worker_fns={w.name: ok_fn for w in WORKERS},
                            reviewer_fns={"reviewer": lambda t, ctx: {"verdict": "ok"}})
        self.assertEqual(res.zone, "purple")

    def test_trail_records_route(self):
        self.co.route(Task(name="t", risk="low", requires=("lookup",)),
                      worker_fns={w.name: ok_fn for w in WORKERS}, self_exec=ok_fn)
        self.assertEqual(len(self.trail.entries), 1)
        ok, _, total = self.trail.verify()
        self.assertTrue(ok)
        self.assertEqual(total, 1)
        self.assertEqual(self.trail.entries[0]["event"], "route")


if __name__ == "__main__":
    unittest.main()