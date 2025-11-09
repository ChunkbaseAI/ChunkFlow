# Chunkbase File Brain

Local-first CLI that crawls your macOS folders, extracts text and metadata from common document formats, and answers natural-language queries using BM25. Day‑1 focuses on keyword relevance + a recency tie-breaker so prompts like “latest PRD” surface the newest matching files.

## Features

- Crawl configurable roots (defaults: `~/Downloads`, `~/Documents`, `~/Desktop`) with ignore globs (`.git`, `node_modules`, `Library`).
- Parse PDF (PyMuPDF), DOCX (python-docx), Markdown/Text (UTF‑8), with optional PaddleOCR fallback for scanned PDFs.
- Build a document-level BM25S index (falls back to `rank_bm25` if needed); metadata persisted under `data/`.
- Query with natural language; automatic recency tie-breaker when queries include “latest”, “recent”, or “newest”.
- Timing insights from the CLI: crawl, index build, and query latency in milliseconds.

## Installation

```bash
git clone https://github.com/ChunkbaseAI/ChunkFlow.git
cd chunkbase-filebrain

# Create and activate the environment
uv venv
source .venv/bin/activate

# Install dependencies
uv pip install -r pyproject.toml
```

Optional (for OCR fallback):

```bash
uc add paddleocr
```

## Quick Start

```bash
# Index default roots with OCR disabled (fastest path)
python cli.py index

# Index with OCR fallback (requires paddleocr)
python cli.py index --ocr paddle

# Query the index
python cli.py find "latest resume"
python cli.py find "product requirement document"
```

Outputs include ranked matches with BM25 scores, file paths, modified timestamps, and the time the query took to execute.

## Configuration

- **Roots:** Pass multiple paths to `index` (`python cli.py index ~/Projects ~/Notes`).
- **Ignore list:** Provide an overrides file via `--ignore-config path/to/ignores.json`.
- **Extensions:** Restrict indexing to specific suffixes (`--extensions .pdf .md`).
- **OCR:** `--ocr paddle` enables PaddleOCR fallback when native extraction fails.

All metadata and indices are stored under `data/`:
- `documents.json` – raw crawl output with path, extension, size, created/modified/accessed times.
- `bm25_metadata.json` – filtered documents that contributed text to the index.
- `bm25s.npz` – serialized BM25S model (or pickle if using `rank_bm25` fallback).

## Project Layout

```
cli.py                     # Typer CLI entry point
chunkbasefb/
  crawl.py                 # File-system crawler & metadata collector
  parse.py                 # Format-specific text extraction + optional OCR
  bm25.py                  # BM25 indexing and search helpers
  utils.py                 # Shared utilities (path expansion, ignores, formatting)
data/                      # Generated indexes + metadata (gitignored except .gitkeep)
examples/                  # Sample docs (to be populated)
tests/                     # Pytest suite (Day‑1 includes an end-to-end smoke test)
```

## Development

```bash
uv pip install -r pyproject.toml
pytest
```

Future days (per roadmap) will layer in semantic embeddings, hybrid fusion, neural reranking, and richer relevance priors.

## Roadmap Snapshot

1. **Day 1** – BM25 baseline (this repo state).
2. Day 2 – Semantic search (Cohere embeddings or local fallback).
3. Day 3 – Hybrid retrieval via RRF.
4. Day 4 – Neural reranking (Cohere Rerank / local cross-encoder).
5. Day 5 – Relevance priors, intent parsing, evaluation harness.