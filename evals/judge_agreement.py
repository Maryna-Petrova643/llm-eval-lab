"""Measure how well the LLM judge agrees with human labels. Don't trust a judge you haven't validated.

Usage:
    python -m evals.judge_agreement results/<run>.json data/human_labels/support_triage_reply_labels.csv
"""
import csv
import json
import sys
from pathlib import Path


def cohens_kappa(pairs: list[tuple[int, int]]) -> float:
    n = len(pairs)
    observed = sum(h == j for h, j in pairs) / n
    p_h = sum(h for h, _ in pairs) / n
    p_j = sum(j for _, j in pairs) / n
    expected = p_h * p_j + (1 - p_h) * (1 - p_j)
    return 1.0 if expected == 1 else (observed - expected) / (1 - expected)


def main(run_path: str, labels_path: str) -> None:
    run = json.loads(Path(run_path).read_text(encoding="utf-8"))
    judge = {r["id"]: int(r["judge"]["pass"]) for r in run["results"]
             if r.get("judge") and r["judge"].get("pass") is not None}
    with open(labels_path, encoding="utf-8") as f:
        human = {row["id"]: int(row["human_pass"]) for row in csv.DictReader(f)}

    ids = sorted(set(judge) & set(human))
    if not ids:
        sys.exit("No overlapping case IDs with judge verdicts and human labels.")
    pairs = [(human[i], judge[i]) for i in ids]
    agreement = sum(h == j for h, j in pairs) / len(pairs)
    kappa = cohens_kappa(pairs)

    fp = [i for i in ids if human[i] == 0 and judge[i] == 1]  # judge too lenient
    fn = [i for i in ids if human[i] == 1 and judge[i] == 0]  # judge too strict

    print(f"Cases compared: {len(ids)}")
    print(f"Raw agreement:  {agreement:.0%}")
    print(f"Cohen's kappa:  {kappa:.2f}  (≥ 0.6 is a reasonable bar before trusting the judge)")
    print(f"Judge passed but human failed (too lenient): {', '.join(fp) or '-'}")
    print(f"Judge failed but human passed (too strict):  {', '.join(fn) or '-'}")
    print("\nRead the disagreements, then tighten the rubric wording and re-check on a held-out set.")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
