# -*- coding: utf-8 -*-
import unittest

from routegrid.models import AgentSpec, Task
from routegrid.policy import ZonePolicy


class ZonePolicyTests(unittest.TestCase):
    def setUp(self):
        self.p = ZonePolicy(panel_size=2)

    def test_green_for_low(self):
        self.assertEqual(self.p.zone_for(Task(name="t", risk="low")), "green")

    def test_yellow_for_medium(self):
        self.assertEqual(self.p.zone_for(Task(name="t", risk="medium")), "yellow")

    def test_red_for_high_and_critical(self):
        self.assertEqual(self.p.zone_for(Task(name="t", risk="high")), "red")
        self.assertEqual(self.p.zone_for(Task(name="t", risk="critical")), "red")

    def test_purple_for_training(self):
        self.assertEqual(self.p.zone_for(Task(name="t", risk="low", opts=("training",))), "purple")
        self.assertEqual(self.p.zone_for(Task(name="t", risk="medium", opts=("mentor",))), "purple")

    def test_describe_strategies(self):
        self.assertEqual(self.p.describe(Task(name="t", risk="low"))["strategy"], "self-execute")
        self.assertEqual(self.p.describe(Task(name="t", risk="medium"))["strategy"], "delegate+review")
        self.assertEqual(self.p.describe(Task(name="t", risk="high"))["strategy"], "panel+aggregate")
        self.assertEqual(self.p.describe(Task(name="t", risk="low", opts=("training",)))["strategy"], "mentor")

    def test_panel_members_limited(self):
        cands = [AgentSpec(name="a%d" % i) for i in range(5)]
        picked = self.p.panel_members(Task(name="t", risk="high"), cands)
        self.assertEqual(len(picked), 2)

    def test_panel_members_critical_all(self):
        cands = [AgentSpec(name="a%d" % i) for i in range(4)]
        picked = self.p.panel_members(Task(name="t", risk="critical"), cands)
        self.assertEqual(len(picked), 4)


if __name__ == "__main__":
    unittest.main()