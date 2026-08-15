# anti-slop (Python)

Opinionated Python lint rules rejecting low-evidence and low-signal patterns.

## Development Workflow

- Run test suite: `pytest`
- Run anti-slop self-check: `python -m anti_slop check`
- Run Flake8 check: `flake8 src tests`
- Sync skill assets after modifying `src/anti_slop`: `python scripts/sync-skill-assets.py`

## Rules Standard

Every rule in `anti_slop/rules/` must:
1. Have a corresponding error code (`SLOP001` - `SLOP015`).
2. Implement `BaseRule` and `run(context)`.
3. Provide a helpful, clear message explaining why the pattern is low-evidence and how to fix it with domain types or boundary parsing.
4. Have comprehensive positive and negative test cases in `tests/test_rules/`.
