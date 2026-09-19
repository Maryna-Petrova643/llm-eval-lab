# LLM Eval Lab

A small, readable evaluation harness for AI features, built for product managers who want to *run* evals, not just write about them.

The example task is **support ticket triage** for a fictional app: the model reads a ticket and returns a category, priority, a "needs human" flag, and a first reply. It's a good learning task because it mixes **checkable answers** (was the category right?) with **subjective quality** (was the reply good?), so you practice both kinds of evaluation.

## What you'll learn

| Concept | Where it lives |
|---|---|
| Golden dataset with slices (happy path, edge, adversarial, multilingual) | `data/golden/support_triage.jsonl` |
| Fast deterministic code checks (format, allowed values, no PII, no promises) | `evals/checks.py` |
| LLM-as-judge with a written rubric | `evals/judge.py`, `rubrics/reply_quality.md` |
| Comparing prompt versions and spotting regressions | `evals/compare_runs.py` |
| Validating the judge against human labels (agreement + Cohen's kappa) | `evals/judge_agreement.py` |
| Error analysis workflow | `docs/error-analysis-guide.md` |

## Setup (Windows, VS Code terminal)

```powershell
git clone https://github.com/Maryna-Petrova643/llm-eval-lab.git
cd llm-eval-lab
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env     # then open .env and paste your Anthropic API key
```

On macOS/Linux use `source .venv/bin/activate` and `cp` instead.

## Run it

**1. Free practice run (no API key, fake model):**
```powershell
python -m evals.run_eval --prompt prompts/triage_v1.md --mock
```
Mock mode exercises every part of the pipeline with deliberately imperfect fake outputs. It ignores the prompt, so use it to learn the workflow, not to compare prompts.

**2. Real run, code checks only (cheapest):**
```powershell
python -m evals.run_eval --prompt prompts/triage_v1.md --no-judge
```

**3. Full run with the LLM judge:**
```powershell
python -m evals.run_eval --prompt prompts/triage_v1.md
python -m evals.run_eval --prompt prompts/triage_v2.md
```

**4. Compare the two prompt versions:**
```powershell
python -m evals.compare_runs results\triage_v1_<timestamp>.json results\triage_v2_<timestamp>.json
```

**5. Check whether the judge agrees with you:**
Open the latest results file, read each reply, and record your own pass/fail in `data/human_labels/support_triage_reply_labels.csv` (the included labels are only an example). Then:
```powershell
python -m evals.judge_agreement results\triage_v2_<timestamp>.json data\human_labels\support_triage_reply_labels.csv
```

**6. Run the unit tests:**
```powershell
python -m pytest
```

## Suggested exercises

1. Run v1 and v2. Which slices (tags) improved? Did anything regress?
2. Read every failure and follow `docs/error-analysis-guide.md` to categorize them.
3. Write `prompts/triage_v3.md` that fixes the top failure category. Re-run and compare.
4. Add 10 new cases to the golden set, including ones based on failures you found.
5. Swap `EVAL_MODEL` in `.env` for a cheaper or stronger model and compare quality against cost.
6. Label replies yourself, measure judge agreement, and edit the rubric until kappa ≥ 0.6.
7. Adapt the harness to a feature you're building: new dataset, prompt, checks, and rubric.

## Project structure

```
llm-eval-lab/
├── data/
│   ├── golden/support_triage.jsonl          # 20 test cases with expected answers and tags
│   └── human_labels/                        # your pass/fail labels for judge validation
├── prompts/                                 # versioned system prompts (v1 naive, v2 improved)
├── rubrics/reply_quality.md                 # the judge's grading instructions
├── evals/
│   ├── llm.py                               # API wrapper + free mock mode
│   ├── checks.py                            # deterministic checks
│   ├── judge.py                             # LLM-as-judge
│   ├── run_eval.py                          # main runner → results/*.json
│   ├── compare_runs.py                      # A/B two runs case by case
│   └── judge_agreement.py                   # judge vs. human agreement + kappa
├── tests/test_checks.py
├── docs/error-analysis-guide.md
└── results/                                 # run outputs (git-ignored)
```

## Good practices built in

- Code checks run before the judge: cheap failures are caught without paying for an LLM call.
- The judge model defaults to a different model than the one being tested, which reduces self-preference bias.
- Results are broken down by tag, because an average can hide a failing slice (like prompt injection).
- Comparisons list regressions explicitly, since a higher average can still break cases that used to pass.
- Your API key lives in `.env`, which is git-ignored. Never commit it.
