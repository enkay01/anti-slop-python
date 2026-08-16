---
name: install-anti-slop
description: Check or configure opinionated Python anti-slop lint rules on a repository directly from this skill. Runs checks without modifying or polluting the target repository.
---

# Anti-Slop (Python)

Opinionated Python lint rules rejecting low-evidence and low-signal patterns.

This skill is a self-contained agent capability. The anti-slop engine and rule implementations live inside this skill and execute directly against any target Python project.

> [!IMPORTANT]
> **Zero Working-Tree Pollution Rule**:
> When using this skill on a repository, **DO NOT copy files or create a `tools/` folder in the target working tree**. The skill already bundles the complete engine. Run the checks directly using the skill script.

---

## 1. Running Checks (Default Workflow)

Run the bundled check script directly against the target repository:

```bash
# Run against the entire repository
python <skill-directory>/scripts/check.py <target-path>

# Run against a specific subfolder (e.g. src/)
python <skill-directory>/scripts/check.py <target-path>/src

# Run with JSON output for automated processing
python <skill-directory>/scripts/check.py <target-path> --format json
```

* **No Working-Tree Changes**: Analyzes files in-place without adding any files or directories.
* **Auto-Discovery**: Automatically uses the target project's `pyproject.toml` rules and ignore patterns if configured; otherwise applies default strict rules.

---

## 2. Optional: Custom Configuration in `pyproject.toml`

If a project wants to customize rule severities or configure boundary modules, add a `[tool.anti-slop]` section to `pyproject.toml`:

```toml
[tool.anti-slop]
ignore_patterns = [
    ".venv/**",
    ".git/**",
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
"no-unknown-parameters" = "error"
"no-unknown-returns" = "error"
"no-unknown-type-aliases" = "error"
"no-unsafe-dictionary-type" = "error"
"no-widen-then-assert" = "error"
"require-safety-comment-for-type-assertion" = { severity = "error", options = { boundary_modules = ["src/adapters/**"] } }
"no-excessive-parameters" = "error"
"require-keyword-only-booleans" = "error"
"no-silent-exception-swallow" = "error"
"no-unnamed-tuple-returns" = "error"
"no-assert-validation" = "error"
"no-mutable-default-arguments" = "error"
"no-excessive-optional-fields" = "error"
"no-test-setup-bloat" = "error"
```

---

## Remediation Guidance for Coding Agents

When fixing anti-slop violations, agents must resolve root architectural causes rather than applying superficial syntactic dodges.

### Critical Anti-Patterns to Avoid (Agent Red Flags)

* **DO NOT delete annotations to bypass Any checks**: Missing annotations on public functions are flagged (SLOP010/SLOP011). Provide concrete domain contracts.
* **DO NOT substitute monkeypatching or direct mock assignment for seams**: In tests, do not assign `mod.fn = MagicMock()` or use `monkeypatch.setattr`. Use constructor-injected test doubles conforming to a `typing.Protocol`.
* **DO NOT substitute reflection with `__dict__` or `vars()`**: Accessing `obj.__dict__[k]` or `vars(obj)[k]` is flagged (SLOP007). Use typed attribute access or literal `getattr(obj, "field", default)`.
* **DO NOT use dummy assignment to swallow exceptions**: Writing `ignored = True` or `logger.debug("skip")` without exc_info is flagged (SLOP018). Use `contextlib.suppress(SpecificException)` for intentional ignores, or chain exceptions with `raise CustomError(...) from err`.
* **DO NOT rename anemic models to fake partials**: Models with >=4 fields where >=50% are optional are flagged (SLOP022). Use `TypedDict(total=False)` for sparse dictionaries or construct complete domain models.
* **DO NOT inline massive model constructors in tests**: Inline instantiations with >5 kwargs in test functions are flagged (SLOP023). Extract typed helper functions with baseline defaults.
* **DO NOT suppress rules with comments**: `# SAFETY:` comments do not bypass production `assert` or `cast()` rules.

---

### Idiomatic Remediation by Category

#### Category 1: Typing Integrity & Boundary Contracts

* **`no-chained-type-assertions` (SLOP001) & `no-widen-then-assert` (SLOP014)**:
  - *Remedy*: Construct target domain types directly or invoke a boundary parser/validator (`TargetType.from_raw(value)`) instead of cascading `cast()`.
* **`no-unsafe-dictionary-type` (SLOP013) & `no-known-value-widening` (SLOP003)**:
  - *Remedy*: Replace loose `dict[str, Any]` contracts with `TypedDict`, `@dataclass(frozen=True)`, or Pydantic models.
* **`no-object-parameters` (SLOP005) & `no-unknown-parameters/returns/type-aliases` (SLOP010/SLOP011/SLOP012)**:
  - *Remedy*: Annotate all public boundaries. Replace untyped `Any`/`object` with explicit `typing.Protocol` interfaces or bounded type parameters (`[T: SupportsProcessing]`).
* **`require-safety-comment-for-type-assertion` (SLOP015)**:
  - *Remedy*: Avoid `cast()`. If casting is strictly required in external adapter code, configure `boundary_modules = ["src/adapters/**"]`.

#### Category 2: Dynamic Reflection & Testing Seams

* **`no-module-mocking` (SLOP004)**:
  - *Remedy*: Refactor code to accept dependencies via constructor injection. In tests, supply an in-memory test double conforming to the `Protocol`.
* **`no-test-setup-bloat` (SLOP023)**:
  - *Remedy*: Extract localized typed helper functions (e.g. `make_model(...)`) with baseline defaults, or use `dataclasses.replace` / `Unpack[TypedDict]`. Avoid inline 15-argument constructor bloat in test functions.
* **`no-reflect-apply` (SLOP006) & `no-reflect-get` (SLOP007)**:
  - *Remedy*: Use direct typed attribute access (`obj.field`), literal `getattr(obj, "field", default)` for optional access, or structural pattern matching (`match item:`).
* **`no-conditional-empty-object-spread` (SLOP002)**:
  - *Remedy*: Construct dictionaries with explicit updates: `payload = dict(base); if condition: payload.update(extra)`.

#### Category 3: API Signatures, Error Flow & Control Flow

* **`no-runtime-typeof` (SLOP008)**:
  - *Remedy*: Avoid exact identity checks (`type(x) is Foo` or `x.__class__ is Foo`). Use `isinstance()`, structural pattern matching (`match/case`), or polymorphic protocols.
* **`no-excessive-parameters` (SLOP016)**:
  - *Remedy*: Group parameters into a dedicated `@dataclass(frozen=True)` options object (`ExportOptions`).
* **`require-keyword-only-booleans` (SLOP017)**:
  - *Remedy*: Make boolean arguments keyword-only: `def process(user_id: str, *, dry_run: bool = False):`.
* **`no-silent-exception-swallow` (SLOP018)**:
  - *Remedy*: Handle specific exceptions, log with `logger.exception()`, use `contextlib.suppress(SpecificException)`, or chain exceptions: `raise ServiceError(...) from err`.
* **`no-unnamed-tuple-returns` (SLOP019)**:
  - *Remedy*: Return a named `@dataclass(frozen=True)` or `NamedTuple` instead of `tuple[bool, str, int]`.
* **`no-assert-validation` (SLOP020)**:
  - *Remedy*: Replace production `assert` with explicit `if condition: raise ValueError(...)`.
* **`no-mutable-default-arguments` (SLOP021)**:
  - *Remedy*: Use `items: list[str] | None = None` and instantiate inside the function, or `field(default_factory=list)`.
* **`no-excessive-optional-fields` (SLOP022)**:
  - *Remedy*: Parse raw boundary data into complete domain models where required fields are non-optional. For sparse dictionaries, use `TypedDict(total=False)`.
