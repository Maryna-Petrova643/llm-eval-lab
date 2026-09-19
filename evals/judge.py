"""LLM-as-judge: grades subjective quality (the reply) against a written rubric."""
import json
from pathlib import Path

from evals.checks import parse_json
from evals.llm import call_model

RUBRIC_PATH = Path(__file__).resolve().parent.parent / "rubrics" / "reply_quality.md"


def judge_reply(ticket: str, reply: str, judge_model: str, mock: bool = False) -> dict:
    rubric = RUBRIC_PATH.read_text(encoding="utf-8")
    message = f"<ticket>\n{ticket}\n</ticket>\n\n<reply>\n{reply}\n</reply>"
    raw = call_model(rubric, message, judge_model, mock=mock)
    verdict = parse_json(raw)
    if verdict is None or "pass" not in verdict:
        return {"pass": None, "reasoning": f"Judge returned unparseable output: {raw[:200]}", "failed_criteria": []}
    return verdict
