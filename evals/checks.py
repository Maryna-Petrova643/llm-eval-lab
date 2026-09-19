"""Fast, deterministic code checks. Run these before any expensive LLM judge."""
import json
import re

ALLOWED = {
    "category": {"billing", "bug", "how_to", "account_access", "feature_request", "other"},
    "priority": {"low", "medium", "high", "urgent"},
}

CARD_NUMBER = re.compile(r"\b(?:\d[ -]?){13,16}\b")
PROMISE_WORDS = re.compile(r"\b(refund(ed)? (has been|is) (issued|processed)|free (month|year)|we will refund|guarantee)\b", re.I)


def parse_json(raw: str) -> dict | None:
    """Return the parsed object if the output is valid JSON, else None. Strict: no surrounding prose."""
    try:
        obj = json.loads(raw.strip())
        return obj if isinstance(obj, dict) else None
    except (json.JSONDecodeError, AttributeError):
        return None


def run_checks(output: dict | None, expected: dict) -> dict:
    """Return a dict of check_name -> bool."""
    if output is None:
        return {"valid_json": False}

    reply = str(output.get("reply", ""))
    results = {
        "valid_json": True,
        "has_all_fields": all(k in output for k in ("category", "priority", "needs_human", "reply")),
        "category_allowed": output.get("category") in ALLOWED["category"],
        "priority_allowed": output.get("priority") in ALLOWED["priority"],
        "category_correct": output.get("category") == expected["category"],
        "priority_correct": output.get("priority") == expected["priority"],
        "needs_human_correct": output.get("needs_human") == expected["needs_human"],
        "reply_under_80_words": len(reply.split()) <= 80,
        "no_card_number_in_reply": not CARD_NUMBER.search(reply),
        "no_promises_in_reply": not PROMISE_WORDS.search(reply),
    }
    return results
