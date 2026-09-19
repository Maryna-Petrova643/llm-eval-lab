"""Compare two eval runs case by case (e.g. prompt v1 vs v2).

Usage:
    python -m evals.compare_runs results/triage_v1_....json results/triage_v2_....json
"""
import json
import sys
from pathlib import Path


def main(a_path: str, b_path: str) -> None:
    a = json.loads(Path(a_path).read_text(encoding="utf-8"))
    b = json.loads(Path(b_path).read_text(encoding="utf-8"))
    print(f"A: {a['prompt']} ({a['model']})  pass rate {a['summary']['overall_pass_rate']:.0%}")
    print(f"B: {b['prompt']} ({b['model']})  pass rate {b['summary']['overall_pass_rate']:.0%}\n")

    a_by_id = {r["id"]: r for r in a["results"]}
    fixed, broken = [], []
    for r in b["results"]:
        prev = a_by_id.get(r["id"])
        if prev is None:
            continue
        if not prev["pass"] and r["pass"]:
            fixed.append(r["id"])
        elif prev["pass"] and not r["pass"]:
            broken.append(r["id"])

    print(f"Fixed by B ({len(fixed)}): {', '.join(fixed) or '-'}")
    print(f"Regressed in B ({len(broken)}): {', '.join(broken) or '-'}")
    if broken:
        print("\nReview regressions before shipping B — a higher average can still hide new failures.")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
