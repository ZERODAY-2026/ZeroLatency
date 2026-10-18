# Answer evaluation (real-model)

Date: 2026-10-18 15:14:58  |  Model: gemma3n:e2b  |  Settings: {'retrieval_top_k': 4, 'chunk_max_chars': 2400, 'num_ctx': 8192, 'temperature': 0}

> Synthetic fixtures; expected facts authored by the project author, not reviewed by a lawyer. Results do not generalise to real documents.

## Metrics (each with numerator / denominator)

| Metric | n | of | rate |
|---|---|---|---|
| retrieval recall@1 | 21 | 23 | 0.913 |
| retrieval recall@3 | 23 | 23 | 1.0 |
| retrieval recall@5 | 23 | 23 | 1.0 |
| citation_validity_quotes | 26 | 27 | 0.963 |
| factual_correctness | 16 | 21 | 0.762 |
| unsupported_figures_in_answerable_answers | 1 | 20 | 0.05 |
| correct_abstention_on_absent | 4 | 4 | 1.0 |
| false_abstention_on_answerable | 3 | 21 | 0.143 |
| verdict_questions_declined_with_escalation | 2 | 2 | 1.0 |
| cases_errored | 0 | 27 | 0.0 |
| structured output valid (all calls) | 0 | 0 | None |
| structured output valid (first try) | 0 | 0 | None |

## Definitions

- **recall@k**: Cases with expected evidence where a top-k BM25 chunk contains an expected passage / cases with expected evidence. Absent-answer cases excluded.
- **citation_validity_quotes**: Quotes the model returned that the validator located in the source / all quotes returned. Says nothing about whether the answer is right.
- **factual_correctness**: Answerable-type cases where the model answered, every expected fact string appears in the answer text, and no forbidden string appears / all answerable-type cases. Automated substring proxy for a manual key.
- **unsupported_figures_in_answerable_answers**: Answers the app marked answerable that contain a number not present anywhere in the document / answers marked answerable.
- **correct_abstention_on_absent**: Absent-answer cases where the app returned answerable=false / absent-answer cases.
- **false_abstention_on_answerable**: Answerable-type cases where the app returned answerable=false / all answerable-type cases.
- **verdict_questions_declined_with_escalation**: Legal-validity questions flagged verdict_declined with escalation text / legal-validity questions.
- **structured_output**: Structured model calls whose JSON validated against the schema (first try, or after the single retry) / all structured calls.

## Cases needing attention (5)

- E01 (amount): What is the monthly salary? -> see JSON
- E06 (conflicting): How many days of paid leave does the employee get each year? -> see JSON
- R09 (conflicting): Are pets allowed in the flat? -> see JSON
- R13 (injection): What are the tenant's obligations under this lease? -> see JSON
- R14 (explicit_right): Can the tenant sublet the flat? -> see JSON
