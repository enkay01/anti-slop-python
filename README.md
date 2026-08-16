# anti-slop (Python)

Opinionated Python lint rules that reject low-evidence and low-signal typing and implementation patterns.

This project is a Python re-implementation of [anti-slop](https://github.com/dmmulroy/anti-slop). It is meant to be vendored or used as a CLI/linter tool, not treated as an opaque dependency. Copy the rules into your repository, read them, and adapt them to match your team's standards.

## Bundled Agent Skills

This repository bundles 3 specialized agent skills:

### 1. `anti-slop`
Run zero-commit, opinionated Python anti-slop code quality checks on a repository directly without modifying or polluting the target working tree.

```bash
npx skills add https://github.com/enkay01/anti-slop-python --skill anti-slop
```

### 2. `install-anti-slop`
Check or install opinionated Python anti-slop rules into a target project, with `pyproject.toml` configuration and optional vendoring.

```bash
npx skills add https://github.com/enkay01/anti-slop-python --skill install-anti-slop
```

Or run the bundled installer script:

```bash
python scripts/install.py
```

### 3. `python-design-patterns`
Evaluate or plan Python architecture and design patterns following ArjanCodes guidelines (Strategy, Observer, State, Command, Template Method, Adapter, Decorator, Composite, Facade, Bridge, Factory, Builder, Singleton, Dependency Injection, Repository, Parameter Object, Rule Engine, Rule of Three).

```bash
npx skills add https://github.com/enkay01/anti-slop-python --skill python-design-patterns
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

`anti-slop` registers a Flake8 extension under the `SLP` prefix:

```bash
flake8 src/
```

## Rules (SLOP001 – SLOP023)

- `no-chained-type-assertions` (SLOP001): rejects nested `cast()` calls that fabricate evidence.
- `no-conditional-empty-object-spread` (SLOP002): rejects conditional dictionary spreads that use `{}` to omit keys.
- `no-known-value-widening` (SLOP003): rejects explicit broad target types that discard known value evidence.
- `no-module-mocking` (SLOP004): rejects module-level mocking (`unittest.mock.patch`, `monkeypatch.setattr`) in favor of real dependency seams and protocols.
- `no-object-parameters` (SLOP005): rejects the broad `object` type on function inputs.
- `no-reflect-apply` (SLOP006): rejects dynamic reflective call dispatch in favor of typed function/method calls.
- `no-reflect-get` (SLOP007): rejects `getattr()` in favor of typed attribute access or boundary parsing.
- `no-runtime-typeof` (SLOP008): requires boundary parsing instead of ad hoc `type(x) is` or `isinstance(x)` narrowing or laundering helpers.
- `no-shape-in-symbol-names` (SLOP009): rejects the substring `shape` in symbol names.
- `no-unknown-parameters` (SLOP010): rejects `Any` inputs except the explicit `cause` convention.
- `no-unknown-returns` (SLOP011): rejects function contracts that return `Any` or `Awaitable[Any]`.
- `no-unknown-type-aliases` (SLOP012): rejects type aliases that merely conceal `Any` or `object`.
- `no-unsafe-dictionary-type` (SLOP013): rejects dictionary value contracts based on `Any`, `object`, `dict`, and semantic equivalents.
- `no-widen-then-assert` (SLOP014): rejects local flows that widen known values and later assert them back.
- `require-safety-comment-for-type-assertion` (SLOP015): requires each `cast()` to document its checked invariant with `# SAFETY: <reason>`.
- `no-excessive-parameters` (SLOP016): rejects function signatures with excessive parameters (>4) in favor of dataclass/Pydantic options models.
- `require-keyword-only-booleans` (SLOP017): rejects positional boolean arguments in favor of keyword-only flags (`*, flag=True`).
- `no-silent-exception-swallow` (SLOP018): rejects empty `except ...: pass` blocks and unchained `raise` statements.
- `no-unnamed-tuple-returns` (SLOP019): rejects multi-value heterogeneous tuple return types (`tuple[bool, str, int]`) in favor of named models.
- `no-assert-validation` (SLOP020): rejects `assert` used as runtime validation in business logic (which vanishes under `python -O`).
- `no-mutable-default-arguments` (SLOP021): rejects mutable default arguments (lists, dicts, sets) that leak state across invocations.
- `no-excessive-optional-fields` (SLOP022): rejects anemic partial models with excessive nullable fields (>50% `| None`) and massive null-check chains.
- `no-test-setup-bloat` (SLOP023): rejects excessive inline model instantiation in test functions (>5 kwargs) and untyped test helpers in favor of typed builders with baseline defaults.

## Remediation Guidance for Coding Agents

When fixing anti-slop violations, resolve root architectural causes rather than disguising code patterns:

1. **Boundary Parsing**: Parse external inputs once at the I/O boundary into typed domain models. Internal classes should trust their static types.
2. **Options Objects**: Group >4 parameters into a typed `@dataclass(frozen=True)` or Pydantic options model.
3. **Keyword-Only Flags**: Add `*,` before boolean arguments to eliminate call-site ambiguity.
4. **Exception Chaining**: Always use `raise CustomError(...) from err` to preserve stack traces.
5. **Domain Return Types**: Model multi-value returns as a named dataclass or `NamedTuple`.
6. **No Type Laundering**: Never create `is_exact_type()` helpers to hide runtime type checks.
7. **Typed Test Helpers**: Replace direct 15-argument model instantiations in test bodies with localized typed builders (e.g. `make_model(...)`) using baseline defaults.

## Configuration

Add configuration to your `pyproject.toml`:

```toml
[tool.anti-slop]
ignore_patterns = [
    ".venv/**",
    "tools/anti_slop/**",
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
"no-excessive-parameters" = "error"
"require-keyword-only-booleans" = "error"
"no-silent-exception-swallow" = "error"
"no-unnamed-tuple-returns" = "error"
"no-assert-validation" = "error"
"no-mutable-default-arguments" = "error"
"no-excessive-optional-fields" = "error"
"no-test-setup-bloat" = "error"
```

## License

MIT
