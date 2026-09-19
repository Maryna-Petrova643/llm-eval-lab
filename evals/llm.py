"""Thin wrapper around the Anthropic API, plus a free offline mock for learning the workflow."""
import json
import os
import random

from dotenv import load_dotenv

load_dotenv()


def call_model(system_prompt: str, user_message: str, model: str, mock: bool = False) -> str:
    """Send one message to a model and return its text response."""
    if mock:
        return _mock_response(system_prompt, user_message)

    import anthropic  # imported here so --mock works without the package configured

    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment
    response = client.messages.create(
        model=model,
        max_tokens=800,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    return "".join(block.text for block in response.content if block.type == "text")


def default_models() -> tuple[str, str]:
    return (
        os.getenv("EVAL_MODEL", "claude-haiku-4-5-20251001"),
        os.getenv("JUDGE_MODEL", "claude-sonnet-5"),
    )


# ---------- Mock mode (no API key, no cost) ----------

_KEYWORDS = {
    "billing": ["charged", "refund", "plan", "billing", "card"],
    "bug": ["crash", "disappeared", "doesn't", "sync", "slow", "error"],
    "account_access": ["log in", "login", "password", "logged into", "email on my account"],
    "feature_request": ["would be great", "would love", "add", "integration"],
    "how_to": ["how do i", "how to", "cómo", "comment", "what's the difference"],
}


def _mock_response(system_prompt: str, user_message: str) -> str:
    """Produce plausible, deliberately imperfect outputs so every part of the pipeline can be exercised."""
    rng = random.Random(user_message)  # deterministic per input
    if "grading" in system_prompt.lower():
        passed = rng.random() > 0.2
        return json.dumps({"reasoning": "Mock judge verdict.", "failed_criteria": [] if passed else [2], "pass": passed})

    text = user_message.lower()
    category = "other"
    for cat, words in _KEYWORDS.items():
        if any(w in text for w in words):
            category = cat
            break
    priority = rng.choice(["low", "medium", "high", "urgent"])
    output = {
        "category": category,
        "priority": priority,
        "needs_human": priority in ("high", "urgent"),
        "reply": "Thanks for reaching out! A teammate will look into this and follow up shortly.",
    }
    raw = json.dumps(output)
    # Occasionally wrap in prose to show why format checks matter
    return f"Here is the triage:\n{raw}" if rng.random() < 0.1 else raw
