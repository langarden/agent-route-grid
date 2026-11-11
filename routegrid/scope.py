# -*- coding: utf-8 -*-
"""Workspace isolation: an agent may only write its own scope (+ declared
shared workspaces). Direct writes anywhere else are denied (fail-closed)."""
from __future__ import annotations

from .models import AgentSpec


class ScopeGuard:
    """Enforces write isolation across agent workspaces."""

    def __init__(self, agents):
        self._owner = {}            # workspace -> owning agent name
        self._shared = {}           # agent name -> set(shared workspaces)
        for agent in agents:
            if agent.scope:
                self._owner[agent.scope] = agent.name
            self._shared[agent.name] = set(agent.shared)

    def owner(self, workspace: str) -> str | None:
        return self._owner.get(workspace)

    def assert_write(self, agent: AgentSpec, workspace: str) -> None:
        """Deny unless the workspace belongs to the agent or is shared."""
        if not workspace:
            raise PermissionError("%s: empty workspace" % agent.name)
        if workspace in self._shared.get(agent.name, set()):
            return
        owner = self._owner.get(workspace)
        if owner is None:
            raise PermissionError("%s: unknown workspace %r" % (agent.name, workspace))
        if owner == agent.name:
            return
        raise PermissionError(
            "%s cannot write workspace %r (owner=%s)" % (agent.name, workspace, owner)
        )

    def can_write(self, agent: AgentSpec, workspace: str) -> bool:
        try:
            self.assert_write(agent, workspace)
            return True
        except PermissionError:
            return False