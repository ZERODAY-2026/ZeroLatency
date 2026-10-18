from .schemas import Answer, TriageResult


def to_markdown(result: TriageResult, answers: list[Answer] | None = None) -> str:
    lines = [f"# Triage report: {result.source_name}", "", f"> {result.disclaimer}", ""]
    lines += ["## Summary", "", result.summary or "No summary available.", ""]
    lines += ["## Candidate findings", ""]
    for number, f in enumerate(result.findings, start=1):
        flag = "verified" if f.verification_status == "verified" else "UNVERIFIED"
        review = " | needs professional review" if f.needs_human_review else ""
        lines += [
            f"### {number}. {f.title} ({f.category}, page {f.page})",
            f"{f.statement_type.capitalize()} | confidence {f.confidence} | {flag}{review}",
            "",
            f.explanation,
            "",
            f"> {f.evidence_quote}",
            "",
            f"_{f.verification_note}_",
            "",
        ]
    lines += ["## Key facts", ""]
    lines += [f"- {k.label}: {k.value} (page {k.page})" for k in result.key_facts] or ["None found."]
    lines += ["", "## Checklist", ""]
    for item in result.checklist:
        where = f"pages {', '.join(map(str, item.pages))}" if item.found else "no matching wording found"
        lines.append(f"- {item.topic}: {where}")
    if answers:
        lines += ["", "## Questions", ""]
        for a in answers:
            lines += [f"**Q: {a.question}**", "", a.answer, ""]
            lines += [f"> {e.quote} (page {e.page}, {e.verification_status})" for e in a.evidence]
            if a.escalation:
                lines += ["", a.escalation]
            lines.append("")
    lines += ["## Limitations", ""] + [f"- {item}" for item in result.limitations]
    return "\n".join(lines) + "\n"
