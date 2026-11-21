# U12 — Judgment evidence UI (110 / 180)

Contract. On the plan sheet (`demo/plan.html` / `plan.js`), judgment patterns show unanswered evidence and accept a local human answer. Does not change `pl check` or write catalog records.

## Behaviour

1. Load `data/pass-report.json` alongside the plan.
2. Pattern cards for 110 Main Entrance and 180 Window Place show `needs judgment` until answered.
3. Activating a judgment pattern opens the inspector with the evidence `question` and controls: **Yes** / **No** / **Clear**.
4. Answers persist in `sessionStorage` under `pl.judgment.<pattern>`.
5. Related diagram features stay highlighted (existing pattern diagram path).

## Non-goals

- Writing answers into check-reports or IFC.
- Blender / MCP / Lean changes.
- Auto-satisfying computed patterns.

## Acceptance

```bash
# manual: python3 demo/serve.py → /plan.html
# select 110 and 180; answer Yes; reload tab keeps answer; Clear resets
uv run pytest tests/test_spatial_lint.py  # no regression
```

## Exit

Draft PR titled `U12 Judgment evidence UI`. Agents do not merge.
