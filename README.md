# anti-slop (Python)

Opinionated Python lint rules that reject low-evidence and low-signal typing and implementation patterns.

This project is a Python re-implementation of [anti-slop](https://github.com/dmmulroy/anti-slop). It is meant to be vendored or used as a CLI/linter tool, not treated as an opaque dependency. Copy the rules into your repository, read them, and adapt them to match your team's standards.

## Installation

### Via Agent Skill

```bash
npx skills add <repository-path> --skill install-anti-slop
```

Or run the bundled installer script:

```bash
python scripts/install.py
```

### Standalone CLI / Package

```bash
pip install -e .
# Or via uv
uv pip install -e .
```

### Run Checks

```bash
anti-slop check
# Or via python module
python -m anti_slop check
```

### Flake8 Integration

`anti-slop` registers a Flake8 extension under the `SLOP` prefix:

```bash
flake8 src/
```

## Rules

- `no-chained-type-assertions` (SLOP001): rejects nested `cast()` calls that fabricate evidence.
- `no-conditional-empty-object-spread` (SLOP002): rejects conditional dictionary spreads that use `{}` to omit keys.
- `no-known-value-widening` (SLOP003): rejects explicit broad target types that discard known value evidence.
- `no-module-mocking` (SLOP004): rejects module-level mocking (`unittest.mock.patch`, `monkeypatch.setattr`) in favor of real dependency seams and protocols.
- `no-object-parameters` (SLOP005): rejects the broad `object` type on function inputs.
- `no-reflect-apply` (SLOP006): rejects dynamic reflective call dispatch in favor of typed function/method calls.
- `no-reflect-get` (SLOP007): rejects `getattr()` in favor of typed attribute access or boundary parsing.
- `no-runtime-typeof` (SLOP008): requires boundary parsing instead of ad hoc `type(x) is` or `isinstance(x)` narrowing.
- `no-shape-in-symbol-names` (SLOP009): rejects the substring `shape` in symbol names.
- `no-unknown-parameters` (SLOP010): rejects `Any` inputs except the explicit `cause` convention.
- `no-unknown-returns` (SLOP011): rejects function contracts that return `Any` or `Awaitable[Any]`.
- `no-unknown-type-aliases` (SLOP012): rejects type aliases that merely conceal `Any` or `object`.
- `no-unsafe-dictionary-type` (SLOP013): rejects dictionary value contracts based on `Any`, `object`, `dict`, and semantic equivalents.
- `no-widen-then-assert` (SLOP014): rejects local flows that widen known values and later assert them back.
- `require-safety-comment-for-type-assertion` (SLOP015): requires each `cast()` to document its checked invariant with `# SAFETY: <reason>`.

## Configuration

Add configuration to your `pyproject.toml`:

```toml
[tool.anti-slop]
ignore_patterns = [
    ".venv/**",
    "tools/anti-slop/**",
]

[tool.anti-slop.rules]
"no-chained-type-assertions" = "error"
"no-conditional-empty-object-spread" = "error"
"no-known-value-widening" = "error"
"no-module-mocking" = "error"
"no-object-parameters" = "error"
"no-reflect-apply" = "error"
"no-reflect-get" = "error"
"no-runtime-typeof" = "error"
"no-shape-in-symbol-names" = "error"
"no-unknown-parameters" = "error"
"no-unknown-returns" = "error"
"no-unknown-type-aliases" = "error"
"no-unsafe-dictionary-type" = "error"
"no-widen-then-assert" = "error"
"require-safety-comment-for-type-assertion" = "error"
```

## License

MIT
