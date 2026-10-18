"""Optional: compare BM25 with a LOCAL embedding retriever on the same CUAD queries.

Embeddings are computed by a local Ollama embedding model over loopback only (assert_loopback_url);
no CUAD text is sent to any hosted service. Cosine search uses FAISS if installed, else numpy.

    ollama pull nomic-embed-text            # setup-time download; any local embedding model works
    python -m eval.retrieval_eval           # writes reports/cuad_retrieval_bm25.json
    python -m eval.embedding_compare --model nomic-embed-text

STATUS: wiring is unit-tested with a fake embedder (tests/test_eval.py). It has NOT been run against a
real embedding model in this repository's recorded results. Do not replace BM25 unless this comparison,
run by you, shows a clear gain at the app's top-k (4) that survives different seeds.
"""

import argparse
import json
import statistics
from collections.abc import Callable

import numpy as np
import requests

from src.privacy import assert_loopback_url
from src.schemas import Chunk

from .retrieval_eval import KS, REPORTS, run, to_markdown

Embedder = Callable[[list[str]], np.ndarray]


def ollama_embedder(model: str, url: str = "http://127.0.0.1:11434", batch: int = 16) -> Embedder:
    base = assert_loopback_url(url)
    session = requests.Session()
    session.trust_env = False

    def embed(texts: list[str]) -> np.ndarray:
        out: list[list[float]] = []
        for i in range(0, len(texts), batch):
            response = session.post(f"{base}/api/embed", json={"model": model, "input": texts[i : i + batch]}, timeout=300)
            response.raise_for_status()
            out.extend(response.json()["embeddings"])
        return np.asarray(out, dtype="float32")

    return embed


class EmbeddingRetriever:
    def __init__(self, chunks: list[Chunk], embed: Embedder):
        self.chunks = chunks
        self.embed = embed
        vectors = self._unit(embed([c.text for c in chunks]))
        try:
            import faiss  # type: ignore[import-not-found]

            self.index = faiss.IndexFlatIP(vectors.shape[1])
            self.index.add(vectors)
            self._faiss = True
        except ImportError:
            self.vectors = vectors
            self._faiss = False

    @staticmethod
    def _unit(matrix: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        return matrix / np.where(norms == 0, 1, norms)

    def search(self, query: str, k: int) -> list[tuple[Chunk, float]]:
        q = self._unit(self.embed([query]))
        k = min(k, len(self.chunks))
        if self._faiss:
            scores, ids = self.index.search(q, k)
            return [(self.chunks[i], float(s)) for i, s in zip(ids[0], scores[0], strict=True) if i >= 0]
        scores = (self.vectors @ q[0]).astype(float)
        order = np.argsort(-scores)[:k]
        return [(self.chunks[i], float(scores[i])) for i in order]


def compare(bm25_rows: list[dict], other_rows: list[dict]) -> dict:
    key = lambda r: (r["contract"], r["category"], r["query_type"])  # noqa: E731
    left, right = {key(r): r for r in bm25_rows}, {key(r): r for r in other_rows}
    shared = sorted(set(left) & set(right))
    out: dict = {"paired_queries": len(shared)}
    for k in KS:
        def hit(row, k=k):
            return bool(row["first_relevant_rank"] and row["first_relevant_rank"] <= k)

        only_bm25 = sum(hit(left[x]) and not hit(right[x]) for x in shared)
        only_other = sum(hit(right[x]) and not hit(left[x]) for x in shared)
        out[f"@{k}"] = {
            "bm25_recall": round(statistics.mean(hit(left[x]) for x in shared), 3) if shared else None,
            "other_recall": round(statistics.mean(hit(right[x]) for x in shared), 3) if shared else None,
            "bm25_only_hits": only_bm25,
            "other_only_hits": only_other,
        }
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="nomic-embed-text")
    parser.add_argument("--url", default="http://127.0.0.1:11434")
    parser.add_argument("--n", type=int, default=40)
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args(argv)
    embed = ollama_embedder(args.model, args.url)
    report = run(args.n, args.seed, f"embedding:{args.model}", lambda chunks: EmbeddingRetriever(chunks, embed))
    stem = REPORTS / f"cuad_retrieval_embedding_{args.model.replace(':', '_')}"
    stem.with_suffix(".json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    stem.with_suffix(".md").write_text(to_markdown(report), encoding="utf-8")
    baseline = REPORTS / "cuad_retrieval_bm25.json"
    if baseline.exists():
        paired = compare(json.loads(baseline.read_text())["rows"], report["rows"])
        (REPORTS / f"cuad_comparison_bm25_vs_{args.model.replace(':', '_')}.json").write_text(json.dumps(paired, indent=1))
        print(json.dumps(paired, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
