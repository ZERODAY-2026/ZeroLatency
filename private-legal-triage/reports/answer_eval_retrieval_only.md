# Answer evaluation (retrieval-only (no model used))

Date: 2026-10-18 07:27:17  |  Model: none  |  Settings: {'retrieval_top_k': 4, 'chunk_max_chars': 2400, 'num_ctx': 8192, 'temperature': 0}

> Synthetic fixtures; expected facts authored by the project author, not reviewed by a lawyer. Results do not generalise to real documents.

## Metrics (each with numerator / denominator)

| Metric | n | of | rate |
|---|---|---|---|
| retrieval recall@1 | 19 | 23 | 0.826 |
| retrieval recall@3 | 23 | 23 | 1.0 |
| retrieval recall@5 | 23 | 23 | 1.0 |

## Definitions

- **recall@k**: Cases with expected evidence where a top-k BM25 chunk contains an expected passage / cases with expected evidence. Absent-answer cases excluded.
- **citation_validity_quotes**: Quotes the model returned that the validator located in the source / all quotes returned. Says nothing about whether the answer is right.
- **factual_correctness**: Answerable-type cases where the model answered, every expected fact string appears in the answer text, and no forbidden string appears / all answerable-type cases. Automated substring proxy for a manual key.
- **unsupported_figures_in_answerable_answers**: Answers the app marked answerable that contain a number not present anywhere in the document / answers marked answerable.
- **correct_abstention_on_absent**: Absent-answer cases where the app returned answerable=false / absent-answer cases.
- **false_abstention_on_answerable**: Answerable-type cases where the app returned answerable=false / all answerable-type cases.
- **verdict_questions_declined_with_escalation**: Legal-validity questions flagged verdict_declined with escalation text / legal-validity questions.
- **structured_output**: Structured model calls whose JSON validated against the schema (first try, or after the single retry) / all structured calls.

## Cases needing attention (0)

