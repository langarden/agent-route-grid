# -*- coding: utf-8 -*-
"""Zone routing policy: maps a task to a route zone.

Zones (aligned with how real teams route work):
  green  - low risk, routine: coordinator executes directly (no delegation)
  yellow - medium risk: delegate to one capable worker, then independent review
  red    - high/critical risk: panel consultation (multiple workers), then
           aggregate; any dissent keeps the result fail-closed
  purple - training / mentorship: route as a learning exercise with a referee
"""
from __future__ import annotations

from typing import Optional

ZONES = ("green", "yellow", "red", "purple")


class ZonePolicy:
    """Deterministic, injectable routing rules."""

    def __init__(self, panel_size: int = 3, training_opt: str = "training"):
        self.panel_size = panel_size
        self.training_opt = training_opt

    def zone_for(self, task) -> str:
        """Return the zone for a task (default deterministic mapping)."""
        if self.training_opt in (task.opts or ()) or "mentor" in (task.opts or ()):
            return "purple"
        if task.risk in ("high", "critical"):
            return "red"
        if task.risk == "medium":
            return "yellow"
        return "green"

    def panel_members(self, task, candidates) -> list:
        """For a red-zone task, pick up to panel_size candidates."""
        if task.risk == "critical":
            return list(candidates)
        return list(candidates[: self.panel_size])

    def describe(self, task) -> dict:
        zone = self.zone_for(task)
        return {
            "zone": zone,
            "strategy": {
                "green": "self-execute",
                "yellow": "delegate+review",
                "red": "panel+aggregate",
                "purple": "mentor",
            }[zone],
        }


DEFAULT_POLICY = ZonePolicy()