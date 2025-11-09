from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Iterable

DEFAULT_IGNORE_GLOBS = {".git", "node_modules", "Library"}


def expand_paths(paths: Iterable[str | Path]) -> list[Path]:
    expanded = []
    for raw in paths:
        path = Path(raw).expanduser().resolve()
        if path.exists():
            expanded.append(path)
    return expanded


def should_ignore(path: Path, ignore_globs: set[str]) -> bool:
    parts = set(part.lower() for part in path.parts)
    return any(glob.lower() in parts for glob in ignore_globs)


def isoformat(ts: float) -> str:
    return datetime.fromtimestamp(ts).isoformat(timespec="seconds")


def load_ignore_globs(config_path: Path | None = None) -> set[str]:
    if not config_path:
        return set(DEFAULT_IGNORE_GLOBS)
    if not config_path.exists():
        return set(DEFAULT_IGNORE_GLOBS)

    try:
        data = json.loads(config_path.read_text())
        custom = set(data.get("ignore", []))
        return set(DEFAULT_IGNORE_GLOBS).union(custom)
    except Exception as exc:  # noqa: BLE001
        logging.getLogger(__name__).warning(
            "Failed to read ignore config %s: %s", config_path, exc
        )
        return set(DEFAULT_IGNORE_GLOBS)