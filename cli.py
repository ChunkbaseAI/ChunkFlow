from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Optional

import typer

from chunkbasefb.bm25 import build_index, search
from chunkbasefb.crawl import crawl_paths
from chunkbasefb.utils import load_ignore_globs

app = typer.Typer(help="Chunkbase File Brain CLI")

DATA_DIR = Path("data")
DOCS_PATH = DATA_DIR / "documents.json"


@app.command()
def index(
    roots: Optional[list[str]] = typer.Argument(
        None, help="Directories to scan; defaults to common user folders."
    ),
    ignore_config: Optional[Path] = typer.Option(
        None, help="Path to JSON file with additional ignore globs."
    ),
    extensions: Optional[list[str]] = typer.Option(
        None, help="Restrict indexing to these file extensions (e.g. --extensions .pdf .docx)."
    ),
    ocr: Optional[str] = typer.Option(
        None,
        help="OCR backend to use when native text extraction fails (e.g. paddle).",
    ),
):
    roots = roots or ["~/Downloads", "~/Documents", "~/Desktop"]
    ignore_globs = load_ignore_globs(ignore_config)
    file_exts = set(extensions) if extensions else None

    DATA_DIR.mkdir(exist_ok=True)

    total_start = time.perf_counter()

    crawl_start = time.perf_counter()
    docs = crawl_paths(roots, ignore=ignore_globs, file_extensions=file_exts)
    crawl_ms = (time.perf_counter() - crawl_start) * 1000

    DOCS_PATH.write_text(json.dumps(docs, indent=2))

    build_start = time.perf_counter()
    build_index(ocr_backend=ocr)
    build_ms = (time.perf_counter() - build_start) * 1000

    total_ms = (time.perf_counter() - total_start) * 1000

    typer.echo(
        f"Indexed {len(docs)} documents -> {DOCS_PATH}\n"
        "BM25 index stored in data/bm25s.npz\n"
        f"Timing: crawl {crawl_ms:.1f} ms | index {build_ms:.1f} ms | total {total_ms:.1f} ms"
    )


@app.command()
def find(query: str, k: int = 25):
    start = time.perf_counter()
    results = search(query, k=k)
    elapsed_ms = (time.perf_counter() - start) * 1000

    if not results:
        typer.echo(f"No matches. Completed in {elapsed_ms:.2f} ms.")
        raise typer.Exit(code=0)

    typer.echo(f"Results ({len(results)} docs) in {elapsed_ms:.2f} ms")

    for idx, doc in enumerate(results, start=1):
        typer.echo(f"{idx}. {doc['basename']}  (score={doc['score']:.3f})")
        typer.echo(f"   path: {doc['path']}")
        typer.echo(f"   modified: {doc['modified_at']}")
        typer.echo("")


if __name__ == "__main__":
    app()