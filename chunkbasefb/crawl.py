from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable

from .utils import expand_paths, isoformat, load_ignore_globs, should_ignore

logger = logging.getLogger(__name__)


def crawl_paths(
    roots: Iterable[str | Path],
    *,
    ignore: set[str] | None = None,
    file_extensions: set[str] | None = None,
) -> list[dict]:
    paths = expand_paths(roots)
    ignore_globs = ignore or load_ignore_globs(None)
    allowed_exts = {ext.lower() for ext in file_extensions} if file_extensions else None

    documents: list[dict] = []
    for root in paths:
        logger.debug("Scanning root %s", root)
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if should_ignore(path, ignore_globs):
                continue
            if allowed_exts and path.suffix.lower() not in allowed_exts:
                continue

            stat = path.stat()
            documents.append(
                {
                    "path": str(path),
                    "basename": path.name,
                    "extension": path.suffix.lower(),
                    "size_bytes": stat.st_size,
                    "modified_at": isoformat(stat.st_mtime),
                    "created_at": isoformat(stat.st_ctime),
                    "accessed_at": isoformat(stat.st_atime),
                }
            )

    logger.info("Discovered %s files across %s roots", len(documents), len(paths))
    return documents