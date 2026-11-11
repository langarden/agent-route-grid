# -*- coding: utf-8 -*-
import unittest

from routegrid.models import AgentSpec, Task


class TaskTests(unittest.TestCase):
    def test_valid_task(self):
        t = Task(name="t1", risk="medium", requires=("lookup",), opts=("batch",))
        self.assertEqual(t.risk, "medium")
        self.assertIn("batch", t.opts)

    def test_bad_risk_rejected(self):
        with self.assertRaises(ValueError):
            Task(name="t", risk="extreme")

    def test_bad_opt_rejected(self):
        with self.assertRaises(ValueError):
            Task(name="t", risk="low", opts=("bogus",))

    def test_as_dict(self):
        d = Task(name="t", risk="high").as_dict()
        self.assertEqual(d["name"], "t")
        self.assertIn("meta", d)


class AgentSpecTests(unittest.TestCase):
    def test_can_and_role(self):
        a = AgentSpec(name="a", roles=("analyst",), capabilities=("lookup",), scope="ws-a")
        self.assertTrue(a.can("lookup"))
        self.assertFalse(a.can("write"))
        self.assertTrue(a.has_role("analyst"))

    def test_review_capable_flag(self):
        a = AgentSpec(name="r", review_capable=True)
        self.assertTrue(a.review_capable)


if __name__ == "__main__":
    unittest.main()