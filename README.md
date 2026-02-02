# Snakebite Community Probe

Snakebite (Broken Arrow — Syntax Pass) is a **community measurement probe**, not a product.

## Goal
Measure, over time:
- How often different AI models emit **syntactically invalid Python**
- How often those errors are **mechanically repairable** using conservative, deterministic rules

This helps answer practical questions like:
- Are cheaper models “good enough” *syntactically*?
- Which syntax error classes are most common?
- Where deterministic repair hits its limits?

## Privacy / data policy (opt-in only)
This project only accepts **metadata**.

We collect:
- `model` (a label you supply)
- syntax validity before/after (`python -m py_compile`)
- error class/text (sanitized)
- count of fixes attempted
- a file hash (sha256)

We do **NOT** collect:
- prompts
- source code
- project context

Participation must be explicit opt-in by the human running the probe.

## How to run
You run Snakebite locally and generate a JSONL file, then submit that JSONL to this repo.

### 1) Generate JSONL locally
Use the runner in Brian’s Project Tracker repo (or any compatible runner):

- `~/Desktop/project_tracker/projects/active/snakebite_broken_arrow_syntax_pass/runner.py`

Example:

```bash
cd ~/Desktop/project_tracker/projects/active/snakebite_broken_arrow_syntax_pass
python3 runner.py --model "my-model" --in ./samples/my-model --out ./runs/my-model.jsonl
```

### 2) Submit results
Create a PR that adds your JSONL under:

```
results/<your-handle>/<YYYY-MM-DD>/<model>.jsonl
```

The validator will reject files containing unexpected fields.

## Repository structure
- `results/` — raw submitted JSONL files (append-only)
- `scripts/validate.py` — schema + safety validation
- `scripts/aggregate.py` — builds human-friendly summaries
- `public/` — generated summary artifacts (markdown + json)

## What “success” looks like
- Boring, reproducible data capture
- Transparent aggregation
- Clear summaries that are useful to humans choosing models by cost

---

Maintainers: community (seeded by Brian / Echo).