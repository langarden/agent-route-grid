# -*- coding: utf-8 -*-
import unittest

from routegrid.models import AgentSpec
from routegrid.scope import ScopeGuard


class ScopeGuardTests(unittest.TestCase):
    def setUp(self):
        self.a = AgentSpec(name="a", scope="ws-a", shared=("ws-shared",))
        self.b = AgentSpec(name="b", scope="ws-b")
        self.g = ScopeGuard([self.a, self.b])

    def test_owner_writes_own(self):
        self.g.assert_write(self.a, "ws-a")  # no raise

    def test_other_agent_denied(self):
        with self.assertRaises(PermissionError):
            self.g.assert_write(self.b, "ws-a")

    def test_shared_workspace_allowed(self):
        self.g.assert_write(self.a, "ws-shared")  # no raise

    def test_unknown_workspace_denied(self):
        with self.assertRaises(PermissionError):
            self.g.assert_write(self.a, "ws-unknown")

    def test_empty_workspace_denied(self):
        with self.assertRaises(PermissionError):
            self.g.assert_write(self.a, "")

    def test_can_write_flag(self):
        self.assertTrue(self.g.can_write(self.a, "ws-a"))
        self.assertFalse(self.g.can_write(self.b, "ws-a"))

    def test_owner_mapping(self):
        self.assertEqual(self.g.owner("ws-a"), "a")
        self.assertIsNone(self.g.owner("ws-nope"))


if __name__ == "__main__":
    unittest.main()