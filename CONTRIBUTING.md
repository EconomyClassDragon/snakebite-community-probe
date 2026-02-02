# Contributing results

## Opt-in requirement
Only submit results you generated yourself with explicit opt-in.

## Where to put files

Add JSONL under:

```
results/<your-handle>/<YYYY-MM-DD>/<model>.jsonl
```

## Validate locally

```bash
python3 scripts/validate.py results
python3 scripts/aggregate.py
```

## What not to submit
- prompts
- source code
- chat logs
- any project context

If your runner includes additional fields, strip them before submitting.
