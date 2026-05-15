"""Type definitions for pydantic-deep."""

from __future__ import annotations

from dataclasses import dataclass as _dataclass
from datetime import datetime
from typing import Any, Literal, TypedDict, TypeVar

from pydantic_ai.output import OutputSpec
from pydantic_ai_backends import (
    EditResult as EditResult,
)
from pydantic_ai_backends import (
    ExecuteResponse as ExecuteResponse,
)
from pydantic_ai_backends import (
    FileData as FileData,
)
from pydantic_ai_backends import (
    FileInfo as FileInfo,
)
from pydantic_ai_backends import (
    GrepMatch as GrepMatch,
)
from pydantic_ai_backends import (
    RuntimeConfig as RuntimeConfig,
)
from pydantic_ai_backends import (
    WriteResult as WriteResult,
)
from pydantic_ai_todo import Todo as Todo
from subagents_pydantic_ai import CompiledSubAgent as CompiledSubAgent
from subagents_pydantic_ai import SubAgentConfig as SubAgentConfig

# Re-export new Skill dataclass from skills package
from pydantic_deep.toolsets.skills.types import Skill as Skill

# Re-export OutputSpec from pydantic-ai for structured output support
ResponseFormat = OutputSpec[object]

# Type variable for output types
OutputT = TypeVar("OutputT")


@_dataclass
class BrowseResult:
    """Result of a browser navigation or interaction.

    Returned by helper utilities that wrap ``BrowserToolset`` tool output
    into a structured form. The toolset tools themselves return plain strings
    for pydantic-ai compatibility; use this dataclass when you want typed
    access to individual fields in your own code.

    Attributes:
        url: The page URL after the action.
        title: The page title.
        content: Page content as Markdown, truncated to ``max_content_tokens``.
        screenshot: Base64-encoded PNG screenshot, or ``None`` if not captured.
        error: Error message if the action failed, or ``None`` on success.
    """

    url: str
    title: str
    content: str
    screenshot: str | None = None
    error: str | None = None


class UploadedFile(TypedDict):
    """Metadata for an uploaded file.

    Uploaded files are stored in the backend and can be accessed by the agent
    through file tools (read_file, grep, glob, execute).
    """

    name: str  # Original filename
    path: str  # Path in backend (e.g., /uploads/sales.csv)
    size: int  # Size in bytes
    line_count: int | None  # Number of lines (for text files)
    mime_type: str | None  # MIME type (e.g., text/plain)
    encoding: str  # Encoding (e.g., utf-8, binary)


# Live Run Forking — Stage 1 kernel types (see issue #102)


@_dataclass(frozen=True)
class BranchSpec:
    """Specification for a single branch in a fork.

    Attributes:
        label: Human-readable branch label (e.g. ``"approach_a"``).
        steer: First user message delivered to the branch agent — the
            instruction that differentiates this branch from siblings.
        model: Optional model override for the branch. ``None`` inherits
            the parent's model.
        budget_usd: Optional per-branch budget. Accepted but **not
            enforced** in Stage 1 — enforcement lands in Stage 4.
        extra_instructions: Optional extra instructions appended to the
            branch's system prompt.
    """

    label: str
    steer: str
    model: str | None = None
    budget_usd: float | None = None
    extra_instructions: str | None = None


@_dataclass(frozen=True)
class BranchIsolation:
    """Isolation flags controlling what state branches share with the parent.

    Defaults match the project's per-branch isolation policy:
    ``history`` always copies; ``backend``, ``memory``, ``todos`` copy by
    default; ``message_queue`` is isolated; ``team_bus`` is shared (peer-to-peer
    bus, branches CAN talk by default).

    Stage 1 fully exercises ``backend="copy"`` and ``message_queue="isolated"``;
    other values are accepted for forward-compat.
    """

    history: Literal["copy"] = "copy"
    backend: Literal["copy", "share_readonly", "share"] = "copy"
    memory: Literal["copy", "share"] = "copy"
    todos: Literal["copy", "share"] = "copy"
    message_queue: Literal["isolated", "shared"] = "isolated"
    team_bus: Literal["shared", "isolated"] = "shared"


@_dataclass
class BranchStatus:
    """Runtime status snapshot of a single branch."""

    id: str
    label: str
    state: Literal["running", "done", "failed", "terminated"]
    current_turn: int
    last_activity_at: datetime
    last_message_preview: str | None = None
    error: str | None = None


@_dataclass(frozen=True)
class MergeStrategy:
    """Merge strategy for resolving a fork.

    Stage 1 supports ``kind="manual"`` only — the agent (or user) picks a
    winner via ``merge_or_select(action="pick:<id>")``. Stage 6 extends this
    to ``"auto"``, ``"auto_with_fallback"``, ``"vote"``.
    """

    kind: Literal["manual"] = "manual"


@_dataclass
class ForkHandle:
    """Handle returned by ``ForkCoordinator.fork()`` identifying a live fork."""

    fork_id: str
    parent_checkpoint_id: str | None
    branches: list[str]
    merge_strategy: MergeStrategy
    created_at: datetime


@_dataclass
class MergeResult:
    """Result returned by ``ForkCoordinator.merge_or_select()``."""

    fork_id: str
    winner_branch_id: str
    discarded_branches: list[str]
    history_after_merge: list[Any]


@_dataclass(frozen=True)
class FileChange:
    """Single overlay write event recorded by ``BranchOverlay``.

    The temporal-ordered ``list[FileChange]`` exposed by ``BranchOverlay.changes()``
    is the data spine consumed by Stage 2's diff, Stage 5's materializer, and
    Stage 6's judge.
    """

    path: str
    op: Literal["write", "edit"]
    timestamp: datetime
