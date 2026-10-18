"""Answer-quality evaluation on synthetic rental and employment documents.

Retrieval, citation validity, factual correctness, unsupported claims, abstention and structured-output
validity are computed and reported SEPARATELY (a matching quote does not prove the interpretation is right).

    python -m eval.answer_eval --retrieval-only              # no model needed; real BM25 numbers
    python -m eval.answer_eval --model gemma3n:e2b           # needs local Ollama + that model
    python -m eval.answer_eval --model gemma3n:e4b --analysis

Expected facts were written by the author of this repository and checked against the fixtures; they have
not been reviewed by a lawyer. "Factual correctness" here is an automated substring proxy for that
manual key (see docs/EVALUATION.md for what it can and cannot detect).
"""

import argparse
import json
import re
import time
from pathlib import Path

from src.chunker import chunk_pages
from src.citation_validator import normalize
from src.config import Settings
from src.document_parser import extract_pages
from src.gemma_client import OllamaClient, StructuredStats
from src.pipeline import DocumentSession
from src.privacy import network_guard
from src.qa import BM25Index

HERE = Path(__file__).resolve().parent
REPORTS = HERE.parent / "reports"
CASES = HERE / "cases" / "synthetic_cases.json"
FIXTURES = HERE / "fixtures"
KS = (1, 3, 5)


def load_cases() -> list[dict]:
    return json.loads(CASES.read_text(encoding="utf-8"))["cases"]


def _flat(text: str) -> str:
    return re.sub(r"[,\s]+", " ", normalize(text)).strip()


def contains_fact(answer: str, fact: str) -> bool:
    haystack = _flat(answer)
    return any(_flat(option) in haystack for option in fact.split("|"))


def share(numerator: int, denominator: int) -> dict:
    return {"n": numerator, "of": denominator, "rate": round(numerator / denominator, 3) if denominator else None}


def retrieval_results(case: dict, chunks, retriever) -> dict:
    if not case["expected_evidence"]:
        return {"applicable": False}
    needles = [normalize(e) for e in case["expected_evidence"]]
    ranked = [c for c, _ in retriever.search(case["question"], max(KS))]
    first = next((i for i, c in enumerate(ranked, 1) if any(n in normalize(c.text) for n in needles)), None)
    return {"applicable": True, "first_relevant_rank": first, **{f"hit@{k}": bool(first and first <= k) for k in KS}}


def run_case(case: dict, session: DocumentSession, retriever, model: str | None) -> dict:
    out = {"id": case["id"], "doc": case["doc"], "type": case["type"], "question": case["question"]}
    out["retrieval"] = retrieval_results(case, session.chunks, retriever)
    if model is None:
        return out
    started = time.perf_counter()
    try:
        answer = session.ask(case["question"], model=model)
    except Exception as error:  # a failed call is a result, not something to hide
        out.update(error=type(error).__name__, error_message=str(error), seconds=round(time.perf_counter() - started, 2))
        return out
    out["seconds"] = round(time.perf_counter() - started, 2)
    verified = [e for e in answer.evidence if e.verification_status == "verified"]
    out["answer"] = {
        "answerable": answer.answerable,
        "text": answer.answer,
        "evidence": [e.model_dump() for e in answer.evidence],
        "verdict_declined": answer.verdict_declined,
        "ungrounded_figures": answer.ungrounded_figures,
        "notes": answer.notes,
    }
    out["citations"] = {"quotes": len(answer.evidence), "verified": len(verified)}
    if case.get("expect_abstain"):
        out["abstained_correctly"] = not answer.answerable
    elif case.get("expected_facts"):
        out["abstained_wrongly"] = not answer.answerable
        out["facts_present"] = {f: contains_fact(answer.answer, f) for f in case["expected_facts"]}
        out["forbidden_present"] = [f for f in case.get("forbidden", []) if contains_fact(answer.answer, f)]
        out["factually_correct"] = answer.answerable and all(out["facts_present"].values()) and not out["forbidden_present"]
    if case.get("expect_verdict_declined"):
        out["verdict_handled"] = answer.verdict_declined and bool(answer.escalation)
    return out


def analysis_metrics(session: DocumentSession, cases: list[dict], model: str | None) -> dict:
    result = session.analyze(model=model)
    seeded = [normalize(e) for case in cases if case["doc"] == session.path.stem for e in case["expected_evidence"]]
    quotes = [normalize(f.evidence_quote) for f in result.findings]

    def overlaps(a: str, b: str) -> bool:
        short, long_ = sorted((a, b), key=len)
        return len(short) >= 20 and any(short[i : i + 20] in long_ for i in range(0, len(short) - 19, 10))

    verified = sum(f.verification_status == "verified" for f in result.findings)
    covered = sum(any(overlaps(s, q) for q in quotes) for s in seeded)
    return {
        "findings": len(result.findings),
        "citation_validity": share(verified, len(result.findings)),
        "unverified_quote_rate": share(len(result.findings) - verified, len(result.findings)),
        "seeded_passage_recall": share(covered, len(seeded)),
        "limitations": result.limitations,
        "seconds": result.elapsed_seconds,
    }


def summarize(results: list[dict], with_model: bool) -> dict:
    applicable = [r for r in results if r["retrieval"].get("applicable")]
    summary: dict = {
        "retrieval": {f"recall@{k}": share(sum(r["retrieval"][f"hit@{k}"] for r in applicable), len(applicable)) for k in KS}
    }
    if not with_model:
        return summary
    answered = [r for r in results if "answer" in r]
    answerable = [r for r in answered if r["answer"]["answerable"]]
    expect_answer = [r for r in answered if "facts_present" in r]
    absent = [r for r in answered if "abstained_correctly" in r]
    verdicts = [r for r in answered if "verdict_handled" in r]
    summary.update(
        {
            "cases_run": len(results),
            "cases_errored": share(len(results) - len(answered), len(results)),
            "citation_validity_quotes": share(sum(r["citations"]["verified"] for r in answered), sum(r["citations"]["quotes"] for r in answered)),
            "factual_correctness": share(sum(r["factually_correct"] for r in expect_answer), len(expect_answer)),
            "unsupported_figures_in_answerable_answers": share(sum(bool(r["answer"]["ungrounded_figures"]) for r in answerable), len(answerable)),
            "correct_abstention_on_absent": share(sum(r["abstained_correctly"] for r in absent), len(absent)),
            "false_abstention_on_answerable": share(sum(r["abstained_wrongly"] for r in expect_answer), len(expect_answer)),
            "verdict_questions_declined_with_escalation": share(sum(r["verdict_handled"] for r in verdicts), len(verdicts)),
        }
    )
    return summary


DEFINITIONS = {
    "recall@k": "Cases with expected evidence where a top-k BM25 chunk contains an expected passage / cases with expected evidence. Absent-answer cases excluded.",
    "citation_validity_quotes": "Quotes the model returned that the validator located in the source / all quotes returned. Says nothing about whether the answer is right.",
    "factual_correctness": "Answerable-type cases where the model answered, every expected fact string appears in the answer text, and no forbidden string appears / all answerable-type cases. Automated substring proxy for a manual key.",
    "unsupported_figures_in_answerable_answers": "Answers the app marked answerable that contain a number not present anywhere in the document / answers marked answerable.",
    "correct_abstention_on_absent": "Absent-answer cases where the app returned answerable=false / absent-answer cases.",
    "false_abstention_on_answerable": "Answerable-type cases where the app returned answerable=false / all answerable-type cases.",
    "verdict_questions_declined_with_escalation": "Legal-validity questions flagged verdict_declined with escalation text / legal-validity questions.",
    "structured_output": "Structured model calls whose JSON validated against the schema (first try, or after the single retry) / all structured calls.",
}


def evaluate(model: str | None, client=None, include_analysis: bool = False, cfg: Settings | None = None) -> dict:
    cfg = cfg or Settings()
    cases = load_cases()
    stats = StructuredStats()
    if model is not None and client is None:
        client = OllamaClient(cfg)
    if client is not None:
        client.stats = stats
    results, analyses = [], {}
    for doc in sorted({c["doc"] for c in cases}):
        path = FIXTURES / f"{doc}.txt"
        session = DocumentSession(path, client or _NoModel(), cfg) if model is not None else _offline_session(path, cfg)
        retriever = BM25Index(session.chunks)
        for case in [c for c in cases if c["doc"] == doc]:
            results.append(run_case(case, session, retriever, model))
        if include_analysis and model is not None:
            analyses[doc] = analysis_metrics(session, cases, model)
    summary = summarize(results, model is not None)
    if model is not None:
        summary["structured_output"] = {
            "all_calls": share(stats.valid, stats.calls),
            "first_try": share(stats.first_try_valid, stats.calls),
            "failed_after_retry": stats.failed,
        }
    return {
        "mode": "real-model" if model is not None else "retrieval-only (no model used)",
        "model": model,
        "date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "settings": {"retrieval_top_k": cfg.retrieval_top_k, "chunk_max_chars": cfg.chunk_max_chars, "num_ctx": cfg.num_ctx, "temperature": 0},
        "definitions": DEFINITIONS,
        "summary": summary,
        "analysis": analyses,
        "cases": results,
    }


class _NoModel:
    def chat_json(self, *a):  # pragma: no cover
        raise RuntimeError("no model configured")


class _OfflineSession:
    def __init__(self, path: Path, cfg: Settings):
        self.chunks = chunk_pages(extract_pages(path, cfg), cfg)


def _offline_session(path: Path, cfg: Settings):
    return _OfflineSession(path, cfg)


def to_markdown(report: dict) -> str:
    s = report["summary"]
    lines = [
        f"# Answer evaluation ({report['mode']})",
        "",
        f"Date: {report['date']}  |  Model: {report['model'] or 'none'}  |  Settings: {report['settings']}",
        "",
        "> Synthetic fixtures; expected facts authored by the project author, not reviewed by a lawyer. Results do not generalise to real documents.",
        "",
        "## Metrics (each with numerator / denominator)",
        "",
        "| Metric | n | of | rate |",
        "|---|---|---|---|",
    ]

    def row(name, d):
        lines.append(f"| {name} | {d['n']} | {d['of']} | {d['rate']} |")

    for name, d in s["retrieval"].items():
        row(f"retrieval {name}", d)
    for name in (
        "citation_validity_quotes", "factual_correctness", "unsupported_figures_in_answerable_answers",
        "correct_abstention_on_absent", "false_abstention_on_answerable",
        "verdict_questions_declined_with_escalation", "cases_errored",
    ):
        if name in s:
            row(name, s[name])
    if "structured_output" in s:
        row("structured output valid (all calls)", s["structured_output"]["all_calls"])
        row("structured output valid (first try)", s["structured_output"]["first_try"])
    for doc, a in report["analysis"].items():
        row(f"analysis[{doc}] citation validity", a["citation_validity"])
        row(f"analysis[{doc}] seeded passage recall", a["seeded_passage_recall"])
    lines += ["", "## Definitions", ""] + [f"- **{k}**: {v}" for k, v in report["definitions"].items()]
    failures = [
        r for r in report["cases"]
        if r.get("error") or r.get("factually_correct") is False or r.get("abstained_correctly") is False
        or r.get("verdict_handled") is False or (r["retrieval"].get("applicable") and not r["retrieval"]["hit@5"])
    ]
    lines += ["", f"## Cases needing attention ({len(failures)})", ""]
    for r in failures:
        reason = r.get("error") or ("retrieval miss@5" if r["retrieval"].get("applicable") and not r["retrieval"]["hit@5"] else "see JSON")
        lines.append(f"- {r['id']} ({r['type']}): {r['question']} -> {reason}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", help="allowlisted model id, e.g. gemma3n:e2b")
    parser.add_argument("--retrieval-only", action="store_true")
    parser.add_argument("--analysis", action="store_true", help="also run full analysis on each fixture")
    args = parser.parse_args(argv)
    if not args.model and not args.retrieval_only:
        parser.error("choose --retrieval-only or --model <id>")
    REPORTS.mkdir(exist_ok=True)
    with network_guard():
        report = evaluate(None if args.retrieval_only else args.model, include_analysis=args.analysis)
    tag = "retrieval_only" if args.retrieval_only else args.model.replace(":", "_")
    (REPORTS / f"answer_eval_{tag}.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    (REPORTS / f"answer_eval_{tag}.md").write_text(to_markdown(report), encoding="utf-8")
    print(to_markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
