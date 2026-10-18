# Evaluation Methodology and Results

## Overview

Legal document triage evaluation requires distinguishing between three separate components:
1. **Passage Retrieval Quality**: Does the retriever rank relevant legal clauses in the top-k results?
2. **Citation Validity**: Do the citations and quotes produced by the model actually exist in the source document text?
3. **Answer Correctness**: Did the model interpret the clause correctly according to established ground truth?

A matching quotation proves only that the text is present in the document; it does not prove the model's legal conclusion or reasoning is sound.

---

## 1. CUAD Retrieval Benchmark (Commercial Contracts)

### Dataset
- **Source**: Contract Understanding Atticus Dataset (CUAD) `aok_v1.0` (Atticus Project, NeurIPS 2021).
- **Licence**: CC BY 4.0.
- **Evaluation Subset**: 40 randomly sampled commercial contracts (seed 2026) across 21 expert-annotated clause types.
- **Data Integrity**: Source dataset files are kept out of Git. Download script `eval/cuad_setup.py` fetches the official dataset locally for reproducibility.

### Retrieval Metrics (BM25 Baseline)
Evaluated across 678 test queries (339 category queries + 339 detail queries):

| Query Type | Queries | Recall@1 | Chance@1 | Recall@3 | Chance@3 | Recall@5 | Chance@5 | MRR@5 |
|---|---|---|---|---|---|---|---|---|
| **ALL Queries** | 678 | **0.538** | 0.066 | **0.740** | 0.187 | **0.802** | 0.293 | **0.644** |
| Category Name | 339 | 0.543 | 0.066 | 0.717 | 0.187 | 0.773 | 0.293 | 0.636 |
| Clause Details | 339 | 0.534 | 0.066 | 0.764 | 0.187 | 0.832 | 0.293 | 0.653 |

*Key Findings*:
- Top-3 Recall reaches 74.0% (vs 18.7% chance baseline), and Top-5 Recall reaches 80.2% (vs 29.3% chance baseline).
- High-performing clauses: *Insurance* (100% R@1), *No-Solicit* (100% R@1), *Renewal Term* (100% R@3), *Notice Period* (90% R@3), *Governing Law* (86.1% R@3).
- Low-performing clauses: *Covenant Not To Sue* (0.0% category R@1, but 40% with descriptive details), *Exclusivity* (17.6% R@1).
- Full detailed logs: [reports/cuad_retrieval_bm25.md](file:///c:/Users/vgava/Downloads/Backend/private-legal-triage/reports/cuad_retrieval_bm25.md).

---

## 2. Synthetic Q&A Evaluation (Rental & Employment Agreements)

Because CUAD consists exclusively of commercial contracts, synthetic consumer agreements (residential lease and employment contracts) were authored with known ground truth facts, deliberate edge cases, and adversarial prompt injections.

### Metric Definitions
- **Retrieval Recall@k**: Percentage of answerable queries where an expected evidence passage is retrieved in top-k BM25 passages.
- **Citation Validity**: Share of model-returned quotes verified against document text.
- **Factual Correctness**: Percentage of answerable cases where all expected fact substrings appear in the model's answer.
- **Correct Abstention**: Percentage of unanswerable/silent questions where the system correctly abstained (`answerable=false`).
- **Verdict Declination**: Percentage of enforceability/validity questions where the model explicitly declined a legal ruling and provided escalation language.

### Results Summary
- **Retrieval Recall@1**: 82.6% (19/23)
- **Retrieval Recall@3**: 100.0% (23/23)
- **Retrieval Recall@5**: 100.0% (23/23)
- **Real Gemma Citation Validity**: 100.0% (measured during real Gemma 3n E2B execution, 8/8 verified)
- Full detailed report: [reports/answer_eval_retrieval_only.md](file:///c:/Users/vgava/Downloads/Backend/private-legal-triage/reports/answer_eval_retrieval_only.md) and [reports/real_model_run.json](file:///c:/Users/vgava/Downloads/Backend/private-legal-triage/reports/real_model_run.json).

---

## 3. Scope Limitations

1. **CUAD Domain Limitation**: Performance on commercial contracts does not guarantee equal accuracy on consumer leases, employment agreements, or foreign jurisdictions.
2. **Scanned Documents**: The backend does not perform OCR. Scanned or image-only PDFs raise `NoExtractableText`.
3. **Legal Validity**: The tool cannot determine whether a contractual clause is legally binding or enforceable in court. All users are directed to qualified legal counsel.
