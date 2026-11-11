# -*- coding: utf-8 -*-
import unittest

from routegrid.trail import AuditTrail


class TrailTests(unittest.TestCase):
    def test_append_and_verify(self):
        tr = AuditTrail()
        tr.append({"event": "route", "task": "t1"})
        tr.append({"event": "route", "task": "t2"})
        ok, bad, total = tr.verify()
        self.assertTrue(ok)
        self.assertIsNone(bad)
        self.assertEqual(total, 2)

    def test_empty_trail_verifies(self):
        ok, bad, total = AuditTrail().verify()
        self.assertTrue(ok)
        self.assertEqual(total, 0)

    def test_tamper_detected(self):
        tr = AuditTrail()
        tr.append({"event": "route", "task": "t1"})
        tr.append({"event": "route", "task": "t2"})
        tr._entries[1]["task"] = "EVIL"  # leave hash stale
        ok, bad, _ = tr.verify()
        self.assertFalse(ok)
        self.assertEqual(bad, 1)

    def test_entries_snapshot(self):
        tr = AuditTrail()
        tr.append({"event": "route", "task": "t1"})
        snapshot = tr.entries
        self.assertEqual(len(snapshot), 1)
        self.assertIn("entry_hash", snapshot[0])

    def test_hash_chaining(self):
        tr = AuditTrail()
        h0 = tr.append({"event": "a"})
        h1 = tr.append({"event": "b"})
        self.assertNotEqual(h0, h1)
        self.assertEqual(tr._entries[1]["prev_hash"], h0)


if __name__ == "__main__":
    unittest.main()