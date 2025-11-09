from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Iterable, Optional

from .parse import extract_text

logger = logging.getLogger(__name__)

DATA_DIR = Path("data")
DOCS_PATH = DATA_DIR / "documents.json"
INDEX_PATH = DATA_DIR / "bm25s.npz"
METADATA_PATH = DATA_DIR / "bm25_metadata.json"


try:
    from bm25s import BM25

    def _build_bm25(corpus: list[list[str]]) -> BM25:
        model = BM25()
        model.index(corpus)
        return model

    def _save_bm25(model: BM25) -> None:
        model.save(INDEX_PATH.as_posix())

    def _load_bm25():
        return BM25.load(INDEX_PATH.as_posix())

    BM25_AVAILABLE = True
except Exception:  # noqa: BLE001
    from rank_bm25 import BM25Okapi

    def _build_bm25(corpus: list[list[str]]) -> BM25Okapi:
        return BM25Okapi(corpus)

    def _save_bm25(model: BM25Okapi) -> None:
        with INDEX_PATH.open("wb") as fp:
            import pickle

            pickle.dump(model, fp)

    def _load_bm25():
        import pickle

        with INDEX_PATH.open("rb") as fp:
            return pickle.load(fp)

    BM25_AVAILABLE = False


def build_index(*, ocr_backend: Optional[str] = None) -> None:
    if not DOCS_PATH.exists():
        raise FileNotFoundError("documents.json missing. Run `chunkfb index` first.")

    docs = json.loads(DOCS_PATH.read_text())

    corpus: list[list[str]] = []
    metadata: list[dict] = []

    for doc in docs:
        path = Path(doc["path"])
        text = extract_text(path, ocr_backend=ocr_backend)
        if not text.strip():
            continue

        tokens = _tokenize(text)
        if not tokens:
            continue

        corpus.append(tokens)
        metadata.append({**doc, "num_terms": len(tokens)})

    if not corpus:
        raise ValueError("No documents with text content to index.")

    model = _build_bm25(corpus)
    DATA_DIR.mkdir(exist_ok=True)
    _save_bm25(model)
    METADATA_PATH.write_text(json.dumps(metadata, indent=2))
    logger.info(
        "Built BM25 index over %s documents (%s tokens). Backend=%s",
        len(metadata),
        sum(len(doc) for doc in corpus),
        "bm25s" if BM25_AVAILABLE else "rank_bm25",
    )


def search(query: str, *, k: int = 25, include_latest_boost: bool = True) -> list[dict]:
    if not INDEX_PATH.exists() or not METADATA_PATH.exists():
        raise FileNotFoundError("Index missing. Run `chunkfb index` first.")

    metadata = json.loads(METADATA_PATH.read_text())
    model = _load_bm25()

    tokens = _tokenize(query)
    if not tokens:
        return []

    scores = model.get_scores(tokens)
    ranked = sorted(
        zip(metadata, scores),
        key=lambda pair: float(pair[1]),
        reverse=True,
    )[:k]

    results = [
        {"score": float(score), **doc_meta}
        for doc_meta, score in ranked
    ]

    if include_latest_boost and any(word in query.lower() for word in ("latest", "recent", "newest")):
        results.sort(key=lambda item: item["modified_at"], reverse=True)

    return results

def _tokenize(text: str) -> list[str]:
    return [
        token.lower()
        for token in text.split()
        if token and token.isprintable()
    ]