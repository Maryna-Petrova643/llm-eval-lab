"""Run a prompt version against the golden dataset and save scored results.

Usage:
    python -m evals.run_eval --prompt prompts/triage_v2.md --mock
    python -m evals.run_eval --prompt prompts/triage_v2.md          # real API call
    python -m evals.run_eval --prompt prompts/triage_v2.md --no-judge
"""
import argparse
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from evals.checks import parse_json, run_checks
from evals.judge import judge_reply
from evals.llm import call_model, default_models

ROOT = Path(__file__).resolve().parent.parent


def load_cases(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", required=True, help="Path to the system prompt file")
    parser.add_argument("--data", default="data/golden/support_triage.jsonl")
    parser.add_argument("--mock", action="store_true", help="Use a free offline fake model")
    parser.add_argument("--no-judge", action="store_true", help="Skip the LLM judge (code checks only)")
    args = parser.parse_args()

    eval_model, judge_model = default_models()
    prompt_path = ROOT / args.prompt
    system_prompt = prompt_path.read_text(encoding="utf-8")
    cases = load_cases(ROOT / args.data)

    rows = []
    for case in cases:
        raw = call_model(system_prompt, case["input"], eval_model, mock=args.mock)
        output = parse_json(raw)
        checks = run_checks(output, case["expected"])
        judge = None
        if output and not args.no_judge:
            judge = judge_reply(case["input"], str(output.get("reply", "")), judge_model, mock=args.mock)
        passed = all(checks.values()) and (judge is None or judge.get("pass") is True)
        rows.append({"id": case["id"], "tags": case["tags"], "input": case["input"], "raw_output": raw,
                     "checks": checks, "judge": judge, "pass": passed})
        print(f"{case['id']}: {'PASS' if passed else 'FAIL'}")

    summary = summarize(rows)
    run = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "prompt": args.prompt,
        "model": "mock" if args.mock else eval_model,
        "judge_model": None if args.no_judge else ("mock" if args.mock else judge_model),
        "summary": summary,
        "results": rows,
    }
    out = ROOT / "results" / f"{prompt_path.stem}_{datetime.now():%Y%m%d_%H%M%S}.json"
    out.write_text(json.dumps(run, indent=2, ensure_ascii=False), encoding="utf-8")
    print_summary(summary)
    print(f"\nSaved: {out.relative_to(ROOT)}")


def summarize(rows: list[dict]) -> dict:
    n = len(rows)
    check_rates = defaultdict(int)
    for r in rows:
        for name, ok in r["checks"].items():
            check_rates[name] += int(ok)
    by_tag = defaultdict(lambda: [0, 0])
    for r in rows:
        for t in r["tags"]:
            by_tag[t][0] += int(r["pass"])
            by_tag[t][1] += 1
    judged = [r for r in rows if r["judge"] and r["judge"].get("pass") is not None]
    return {
        "cases": n,
        "overall_pass_rate": round(sum(r["pass"] for r in rows) / n, 3),
        "check_pass_rates": {k: round(v / n, 3) for k, v in check_rates.items()},
        "judge_pass_rate": round(sum(r["judge"]["pass"] for r in judged) / len(judged), 3) if judged else None,
        "pass_rate_by_tag": {t: f"{p}/{c}" for t, (p, c) in sorted(by_tag.items())},
    }


def print_summary(s: dict) -> None:
    print(f"\n=== {s['cases']} cases | overall pass rate {s['overall_pass_rate']:.0%} ===")
    for k, v in s["check_pass_rates"].items():
        print(f"  {k:<26} {v:.0%}")
    if s["judge_pass_rate"] is not None:
        print(f"  {'judge: reply quality':<26} {s['judge_pass_rate']:.0%}")
    print("By tag:", ", ".join(f"{t} {v}" for t, v in s["pass_rate_by_tag"].items()))


if __name__ == "__main__":
    main()
