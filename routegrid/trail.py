# -*- coding: utf-8 -*-
"""Append-only, hash-chained audit trail. Tampering breaks verify()."""
import hashlib
import json
import threading
import time

GENESIS = "0" * 64


def _canonical(event: dict) -> bytes:
    return json.dumps(event, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, default=str).encode("utf-8")


class AuditTrail:
    """JSONL audit log with per-entry sha256 chaining."""

    def __init__(self, path=None):
        self.path = path
        self._lock = threading.Lock()
        self._entries = []
        if path:
            import os
            if os.path.exists(path):
                with open(path, encoding="utf-8") as fh:
                    for line in fh:
                        line = line.strip()
                        if line:
                            self._entries.append(json.loads(line))

    @property
    def entries(self):
        return list(self._entries)

    @property
    def last_hash(self):
        return self._entries[-1]["entry_hash"] if self._entries else GENESIS

    def append(self, event: dict) -> str:
        with self._lock:
            entry = dict(event)
            entry["ts"] = entry.get("ts", time.time())
            entry["prev_hash"] = self.last_hash
            # the digest covers everything EXCEPT entry_hash itself
            digest_input = {k: v for k, v in entry.items() if k != "entry_hash"}
            entry["entry_hash"] = hashlib.sha256(_canonical(digest_input)).hexdigest()
            self._entries.append(entry)
            if self.path:
                with open(self.path, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
            return entry["entry_hash"]

    def verify(self):
        """Return (ok, first_bad_index_or_None, total)."""
        prev = GENESIS
        for i, entry in enumerate(self._entries):
            digest_input = {k: v for k, v in entry.items() if k != "entry_hash"}
            recomputed = hashlib.sha256(_canonical(digest_input)).hexdigest()
            if entry.get("prev_hash") != prev or entry.get("entry_hash") != recomputed:
                return False, i, len(self._entries)
            prev = entry["entry_hash"]
        return True, None, len(self._entries)