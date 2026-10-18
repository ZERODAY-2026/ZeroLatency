"""CUAD-based retrieval evaluation for the application's BM25 retriever (and pluggable alternatives).

What it measures: for a clause-type query on a CUAD contract, does the retriever surface a chunk that
contains expert-labelled text for that clause type within the top k?

What it does NOT measure: answer correctness, citation validity, or performance on consumer rental or
employment agreements (CUAD is commercial contracts; see docs/EVALUATION.md).

Design choices, fixed before looking at any result:
  * Subset: `n` contracts drawn with random.Random(seed) from the alphabetically sorted titles.
  * Categories: a fixed list (CATEGORY_MAP) chosen for relevance to what the application triages.
  * Queries: (a) "category" = the CUAD category name; (b) "details" = the CUAD question's own
    "Details:" sentence. Both are proxies for what a user might ask, not real user questions.
  * Text handling: each contract goes through the SAME code path as an uploaded .txt (extract_pages,
    chunk_pages with default Settings), so chunking effects are included in the numbers.
  * Relevance: a chunk is relevant if its normalized text contains a 40-character window (stride 20) of
    the normalized expert-labelled answer text. Answers shorter than 20 normalized characters are
    excluded (too ambiguous to locate). Queries whose labelled text is found in no chunk are excluded
    and counted.
  * recall@k = share of included queries with >= 1 relevant chunk in the top k. Chance level is reported
    next to it (probability that k chunks drawn at random contain >= 1 relevant chunk).
"""

import argparse
import json
import random
import re
import statistics
import tempfile
from collections import defaultdict
from collections.abc import Callable
from math import comb
from pathlib import Path

from src.chunker import chunk_pages
from src.citation_validator import normalize
from src.config import Settings
from src.document_parser import extract_pages
from src.qa import BM25Index
from src.schemas import Chunk

DATA = Path(__file__).resolve().parent / "data" / "cuad"
REPORTS = Path(__file__).resolve().parents[1] / "reports"
KS = (1, 3, 4, 5)  # 4 is the application's own retrieval_top_k
WINDOW, STRIDE, MIN_GOLD_CHARS = 40, 20, 20

# CUAD expert label -> the application's own finding category. These are different taxonomies; the
# mapping only says which CUAD labels correspond to the kinds of passages the app is meant to surface.
CATEGORY_MAP: dict[str, str] = {
    "Expiration Date": "deadline",
    "Renewal Term": "deadline",
    "Notice Period To Terminate Renewal": "deadline",
    "Warranty Duration": "deadline",
    "Termination For Convenience": "termination",
    "Post-Termination Services": "termination",
    "Change Of Control": "termination",
    "Liquidated Damages": "penalty",
    "Cap On Liability": "penalty",
    "Uncapped Liability": "penalty",
    "Non-Compete": "obligation",
    "Exclusivity": "obligation",
    "Anti-Assignment": "obligation",
    "Audit Rights": "right",
    "Insurance": "obligation",
    "Minimum Commitment": "obligation",
    "No-Solicit Of Employees": "obligation",
    "Non-Disparagement": "obligation",
    "Covenant Not To Sue": "obligation",
    "License Grant": "right",
    "Governing Law": "other",
}
DETAILS = re.compile(r"Details:\s*(.*)$", re.S)

Retriever = Callable[[list[Chunk]], object]  # chunks -> object with .search(query, k)


def load(path: Path = DATA / "CUADv1.json") -> list[dict]:
    if not path.exists():
        raise SystemExit(f"{path} not found. Run: python -m eval.cuad_setup")
    return json.loads(path.read_text(encoding="utf-8"))["data"]


def select_contracts(data: list[dict], n: int, seed: int) -> list[dict]:
    ordered = sorted(data, key=lambda c: c["title"])
    return sorted(random.Random(seed).sample(ordered, min(n, len(ordered))), key=lambda c: c["title"])


def gold_windows(answer_texts: list[str]) -> tuple[list[str], int]:
    windows: list[str] = []
    short = 0
    for text in answer_texts:
        norm = normalize(text)
        if len(norm) < MIN_GOLD_CHARS:
            short += 1
            continue
        if len(norm) <= WINDOW:
            windows.append(norm)
        else:
            windows.extend(norm[i : i + WINDOW] for i in range(0, len(norm) - WINDOW + 1, STRIDE))
    return windows, short


def relevant_chunk_ids(chunks: list[Chunk], windows: list[str]) -> set[str]:
    norm = {chunk.chunk_id: normalize(chunk.text) for chunk in chunks}
    return {cid for cid, text in norm.items() if any(w in text for w in windows)}


def chance_hit(n_chunks: int, n_relevant: int, k: int) -> float:
    k = min(k, n_chunks)
    if n_relevant == 0 or n_chunks == 0:
        return 0.0
    return 1.0 - comb(n_chunks - n_relevant, k) / comb(n_chunks, k)


def queries_for(contract_title: str, qa: dict) -> dict[str, str]:
    category = qa["id"].split("__")[-1]
    match = DETAILS.search(qa["question"])
    return {"category": category, "details": match.group(1).strip() if match else category}


def contract_chunks(text: str, cfg: Settings) -> list[Chunk]:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "contract.txt"
        path.write_text(text, encoding="utf-8")
        return chunk_pages(extract_pages(path, cfg), cfg)


def evaluate(
    contracts: list[dict],
    retriever_factory: Retriever = BM25Index,
    cfg: Settings | None = None,
    categories: dict[str, str] | None = None,
) -> dict:
    cfg = cfg or Settings()
    categories = categories or CATEGORY_MAP
    rows: list[dict] = []
    excluded = {"short_gold_only": 0, "gold_not_locatable": 0, "contract_unreadable": 0}
    chunk_counts: list[int] = []
    for contract in contracts:
        paragraph = contract["paragraphs"][0]
        try:
            chunks = contract_chunks(paragraph["context"], cfg)
        except Exception:
            excluded["contract_unreadable"] += 1
            continue
        chunk_counts.append(len(chunks))
        retriever = retriever_factory(chunks)
        for qa in paragraph["qas"]:
            category = qa["id"].split("__")[-1]
            if category not in categories or qa["is_impossible"] or not qa["answers"]:
                continue
            windows, short = gold_windows([a["text"] for a in qa["answers"]])
            if not windows:
                excluded["short_gold_only"] += 1
                continue
            relevant = relevant_chunk_ids(chunks, windows)
            if not relevant:
                excluded["gold_not_locatable"] += 1
                continue
            for qtype, query in queries_for(contract["title"], qa).items():
                ranked = [c.chunk_id for c, _ in retriever.search(query, max(KS))]
                first = next((i for i, cid in enumerate(ranked, 1) if cid in relevant), None)
                rows.append(
                    {
                        "contract": contract["title"],
                        "category": category,
                        "app_category": categories[category],
                        "query_type": qtype,
                        "n_chunks": len(chunks),
                        "n_relevant": len(relevant),
                        "first_relevant_rank": first,
                        **{f"chance@{k}": chance_hit(len(chunks), len(relevant), k) for k in KS},
                    }
                )
    return {"rows": rows, "excluded": excluded, "chunk_counts": chunk_counts}


def summarize(rows: list[dict]) -> dict:
    def block(subset: list[dict]) -> dict:
        n = len(subset)
        if not n:
            return {"queries": 0}
        out: dict = {"queries": n}
        for k in KS:
            out[f"recall@{k}"] = round(sum(1 for r in subset if r["first_relevant_rank"] and r["first_relevant_rank"] <= k) / n, 3)
            out[f"chance@{k}"] = round(statistics.mean(r[f"chance@{k}"] for r in subset), 3)
        out["mrr@5"] = round(sum(1 / r["first_relevant_rank"] for r in subset if r["first_relevant_rank"]) / n, 3)
        out["mean_relevant_chunks"] = round(statistics.mean(r["n_relevant"] for r in subset), 2)
        return out

    by_type: dict[str, list[dict]] = defaultdict(list)
    by_cat: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in rows:
        by_type[r["query_type"]].append(r)
        by_cat[(r["query_type"], r["category"])].append(r)
    return {
        "overall": block(rows),
        "by_query_type": {t: block(v) for t, v in sorted(by_type.items())},
        "by_category": {f"{t} | {c}": block(v) for (t, c), v in sorted(by_cat.items())},
    }


def to_markdown(report: dict) -> str:
    meta, summ = report["meta"], report["summary"]
    lines = [
        f"# CUAD retrieval evaluation: {meta['retriever']}",
        "",
        "> Generated by `python -m eval.retrieval_eval`. Numbers below are from that run, not hand-edited.",
        "> CUAD is a set of commercial contracts. These results do not show performance on rental or employment agreements.",
        "",
        "## Setup",
        "",
        f"- Dataset: CUAD `{meta['dataset_version']}`, source commit `{meta['snapshot'].get('commit', 'unknown')}`, data.zip sha256 `{meta['snapshot'].get('data_zip_sha256', 'unknown')}`",
        f"- Subset: {meta['contracts_selected']} of {meta['contracts_total']} contracts, `random.Random({meta['seed']}).sample` over alphabetically sorted titles (no manual picking)",
        f"- Contracts evaluated: {meta['contracts_evaluated']}; mean chunks per contract: {meta['mean_chunks']}",
        f"- Retriever: {meta['retriever']}; chunking = application default (chunk_max_chars={meta['chunk_max_chars']})",
        f"- CUAD clause types used ({len(meta['categories'])}): " + ", ".join(f"{c} -> app:{a}" for c, a in meta["categories"].items()),
        f"- Relevance: chunk contains a {WINDOW}-char window of expert-labelled text; labelled answers under {MIN_GOLD_CHARS} chars excluded",
        f"- Excluded: {meta['excluded']}",
        "- Query types: `category` (CUAD label name) and `details` (CUAD's own description sentence)",
        "",
        "## Results (recall@k = share of queries with a relevant chunk in the top k)",
        "",
        "| Query type | Queries | " + " | ".join(f"R@{k} | chance@{k}" for k in KS) + " | MRR@5 | mean relevant chunks |",
        "|---|---|" + "---|---|" * len(KS) + "---|---|",
    ]
    for name, b in [("ALL", summ["overall"]), *summ["by_query_type"].items()]:
        lines.append(
            f"| {name} | {b['queries']} | "
            + " | ".join(f"{b[f'recall@{k}']} | {b[f'chance@{k}']}" for k in KS)
            + f" | {b['mrr@5']} | {b['mean_relevant_chunks']} |"
        )
    lines += ["", "## By clause type", "", "| Query type \\| CUAD label | Queries | R@1 | R@3 | R@5 | chance@3 |", "|---|---|---|---|---|---|"]
    for name, b in summ["by_category"].items():
        lines.append(f"| {name} | {b['queries']} | {b['recall@1']} | {b['recall@3']} | {b['recall@5']} | {b['chance@3']} |")
    lines += ["", "Per-query rows are in the JSON file next to this report (contract ids only; no contract text)."]
    return "\n".join(lines) + "\n"


def run(n: int, seed: int, retriever_name: str = "bm25", factory: Retriever = BM25Index) -> dict:
    data = load()
    chosen = select_contracts(data, n, seed)
    cfg = Settings()
    result = evaluate(chosen, factory, cfg)
    snapshot_path = DATA / "SNAPSHOT.json"
    return {
        "meta": {
            "retriever": retriever_name,
            "dataset": "CUAD",
            "dataset_version": "aok_v1.0",
            "snapshot": json.loads(snapshot_path.read_text()) if snapshot_path.exists() else {},
            "seed": seed,
            "contracts_total": len(data),
            "contracts_selected": len(chosen),
            "contracts_evaluated": len(result["chunk_counts"]),
            "selected_contract_ids": [c["title"] for c in chosen],
            "mean_chunks": round(statistics.mean(result["chunk_counts"]), 1) if result["chunk_counts"] else 0,
            "chunk_max_chars": cfg.chunk_max_chars,
            "categories": CATEGORY_MAP,
            "excluded": result["excluded"],
            "bm25": {"k1": 1.5, "b": 0.75, "stopwords": "built-in list in src/qa.py"},
            "ks": list(KS),
        },
        "summary": summarize(result["rows"]),
        "rows": result["rows"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=40)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--out", type=Path, default=REPORTS / "cuad_retrieval_bm25")
    args = parser.parse_args(argv)
    report = run(args.n, args.seed)
    args.out.parent.mkdir(exist_ok=True)
    args.out.with_suffix(".json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    args.out.with_suffix(".md").write_text(to_markdown(report), encoding="utf-8")
    print(to_markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
