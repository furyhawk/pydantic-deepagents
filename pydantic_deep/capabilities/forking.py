"""Live Run Forking capability — entry point for the kernel.

Adds :class:`LiveForkCapability` to an agent. The capability tracks the
parent run's latest message snapshot (mirroring :class:`CheckpointMiddleware`)
and, on each ``for_run``, allocates a fresh :class:`ForkCoordinator` that
agent-facing tools (``fork_run`` et al.) use to spawn branch tasks.

Concurrent parent runs of the same agent get independent coordinators —
that's what makes Stage 1's isolation primitive thread-safe at the
``agent.run(...)`` level.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

from pydantic_ai import RunContext
from pydantic_ai.capabilities import AbstractCapability
from pydantic_ai.messages import ModelMessage

from pydantic_deep.toolsets.forking.coordinator import ForkCoordinator
from pydantic_deep.toolsets.forking.store import ForkStateStore, InMemoryForkStateStore


@dataclass
class LiveForkCapability(AbstractCapability[Any]):
    """Capability that wires Live Run Forking into an agent.

    Args:
        max_branches: Maximum branches per fork. Stage 1 hard-defaults to ``2``;
            Stage 4 lifts the cap.
        max_depth: Maximum fork nesting depth. Stage 1 hard-defaults to ``1``;
            Stage 4 lifts the cap.
        store: Optional :class:`ForkStateStore`. Defaults to
            :class:`InMemoryForkStateStore` — persistent stores are out of
            scope until after Stage 6.

    The owning agent reference is set by ``create_deep_agent()`` after the
    Agent is constructed (mirrors how ``agent._task_manager`` is set today).
    """

    max_branches: int = 2
    max_depth: int = 1
    store: ForkStateStore | None = None

    _agent_ref: Any = field(default=None, init=False, repr=False)
    _latest_messages: list[ModelMessage] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.store is None:
            self.store = InMemoryForkStateStore()

    @property
    def latest_messages(self) -> list[ModelMessage]:
        """Snapshot of the parent run's most recent message list.

        Returns a copy so callers can't mutate the capability's internal state.
        Updated on every ``before_model_request``; used by ``fork_run`` to
        seed each branch's history at the moment of the fork call.
        """
        return list(self._latest_messages)

    async def for_run(self, ctx: RunContext[Any]) -> LiveForkCapability:
        """Return a fresh per-run capability with an independent coordinator."""
        clone = replace(
            self,
            max_branches=self.max_branches,
            max_depth=self.max_depth,
            store=self.store,
        )
        # init=False fields are reset by replace(); restore the agent ref.
        clone._agent_ref = self._agent_ref

        assert clone.store is not None  # __post_init__ guarantees this
        coordinator = ForkCoordinator(
            agent=clone._agent_ref,
            parent_deps=ctx.deps,
            max_branches=clone.max_branches,
            max_depth=clone.max_depth,
            store=clone.store,
        )
        coordinator.capability = clone
        ctx.deps.fork_coordinator = coordinator
        return clone

    async def before_model_request(
        self,
        ctx: RunContext[Any],
        request_context: Any,
    ) -> Any:
        """Track the latest message snapshot so ``fork()`` can use it."""
        self._latest_messages = list(request_context.messages)
        return request_context


__all__ = ["LiveForkCapability"]
