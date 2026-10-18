import re

from .schemas import ChecklistItem, Page

TOPICS: dict[str, list[str]] = {
    "termination": [r"terminat", r"early exit"],
    "notice period": [r"notice period", r"prior notice", r"written notice", r"days'? notice"],
    "renewal or extension": [r"renew", r"auto-?matic(?:ally)? extend", r"extension of (?:the )?term"],
    "payment terms": [r"\brent\b", r"payment", r"salary", r"fees?\b", r"invoice"],
    "penalties or late fees": [r"penalt", r"late fee", r"liquidated damages", r"forfeit", r"interest on"],
    "security deposit": [r"security deposit", r"deposit"],
    "liability": [r"liabilit", r"liable"],
    "indemnity": [r"indemnif"],
    "confidentiality": [r"confidential", r"non-?disclosure"],
    "assignment or subletting": [r"sub-?let", r"sub-?leas", r"assign"],
    "dispute resolution": [r"arbitrat", r"mediation", r"dispute", r"jurisdiction of"],
    "governing law": [r"governing law", r"governed by", r"laws of"],
    "amendment": [r"amend", r"modif(?:y|ication)", r"variation"],
    "force majeure": [r"force majeure", r"act of god"],
}


def scan_checklist(pages: list[Page]) -> list[ChecklistItem]:
    items: list[ChecklistItem] = []
    for topic, patterns in TOPICS.items():
        combined = re.compile("|".join(patterns), re.I)
        hits = [page.number for page in pages if combined.search(page.text)]
        items.append(ChecklistItem(topic=topic, found=bool(hits), pages=hits))
    return items
