"""Loads the Purpose Team Playbook from disk and caches it in memory.

The entire playbook (~22K tokens) is passed to Claude on every request as a
single cached ``document`` content block. There is no vector DB, no embeddings,
and no chunking - the whole thing fits comfortably in context.

The playbook file is owned by another process and lives at
``knowledge_base/team_playbook.md`` relative to the repository root.
"""

import os
from pathlib import Path

PLAYBOOK_TITLE = "Purpose Team Playbook"

# Repository root is the parent of the hr_assistant package directory.
_REPO_ROOT = Path(__file__).resolve().parent.parent
PLAYBOOK_PATH = _REPO_ROOT / "knowledge_base" / "team_playbook.md"

# Module-level cache of the playbook text (loaded once at startup).
_playbook_cache: str | None = None


class PlaybookError(RuntimeError):
    """Raised when the playbook cannot be loaded."""


def load_playbook(path: os.PathLike | str | None = None) -> str:
    """Load the playbook markdown from disk and cache it in memory.

    Subsequent calls return the cached text. Raises PlaybookError with a clear
    message if the file is missing or empty.
    """
    global _playbook_cache
    if _playbook_cache is not None:
        return _playbook_cache

    playbook_path = Path(path) if path is not None else PLAYBOOK_PATH

    if not playbook_path.exists():
        raise PlaybookError(
            f"Team Playbook not found at {playbook_path}. "
            "The playbook file (knowledge_base/team_playbook.md) must exist "
            "before the bot can answer questions."
        )

    text = playbook_path.read_text(encoding="utf-8")
    if not text.strip():
        raise PlaybookError(
            f"Team Playbook at {playbook_path} is empty. "
            "It must contain the playbook content for the bot to work."
        )

    _playbook_cache = text
    return _playbook_cache


def get_playbook() -> str:
    """Return the cached playbook text, loading it if necessary."""
    return load_playbook()
