---
name: anti-slop
description: Run opinionated Python anti-slop code quality checks on a repository directly from this skill. Use to audit code quality, check PRs, or enforce clean typing and architecture standards without modifying or polluting the target repository.
---

# Anti-Slop (Python)

Opinionated Python lint rules rejecting low-evidence and low-signal patterns.

This skill is a self-contained agent capability. The anti-slop engine and all 21 rule implementations live inside this skill and execute directly against any target Python project.

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

If a project wants to customize rule severities or add custom ignore patterns, add a `[tool.anti-slop]` section to the target repository's `pyproject.toml` (this is purely declarative config; no code files need to be copied):

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
```

---

## 3. Optional: Vendoring (Only When Explicitly Requested)

If and only if the user explicitly asks to vendor the linter into their repository for offline CI builds without installing packages:

```bash
python <skill-directory>/scripts/install.py tools/anti_slop
```

---

## Remediation Guidance for Coding Agents

When fixing anti-slop violations, agents must resolve root architectural causes rather than disguising or laundering code patterns.

### Critical Anti-Patterns to Avoid (Agent Red Flags)

* **DO NOT launder runtime typechecks**: Do not create generic helper functions (e.g. `is_exact_type()`, `check_type()`, `assert_type()`, `verify_type()`) to bypass `no-runtime-typeof`. This merely hides the type check behind an extra layer of abstraction.
* **DO NOT substitute monkeypatching for mocks**: Do not replace `unittest.mock.patch` with `monkeypatch.setattr` or module-level `setattr()`. Use real Dependency Injection with Python protocols.
* **DO NOT substitute reflection with eval or attrgetter**: Do not replace `getattr()` with `operator.attrgetter()`, `operator.methodcaller()`, or `eval()`. Use direct attributes or pattern matching.
* **DO NOT use boilerplate safety comments**: Do not satisfy `require-safety-comment-for-type-assertion` with low-signal comments like `# SAFETY: cast` or `# SAFETY: ok`. State the concrete invariant.
* **DO NOT suppress rules**: Do not add `# noqa`, `# type: ignore`, or mechanically weaken rule severities to make checks pass without fixing the underlying design.

---

### Idiomatic Remediation by Category

#### Category 1: Typing Integrity & Boundary Contracts

* **`no-chained-type-assertions` (SLOP001) & `no-widen-then-assert` (SLOP014)**:
  - *Remedy*: Construct target domain types directly or invoke a boundary parser/validator (`TargetType.from_raw(value)`) instead of cascading `cast()`.
* **`no-unsafe-dictionary-type` (SLOP013) & `no-known-value-widening` (SLOP003)**:
  - *Remedy*: Replace loose `dict[str, Any]` contracts with `TypedDict`, `@dataclass(frozen=True)`, or Pydantic models.
* **`no-object-parameters` (SLOP005) & `no-unknown-parameters/returns/type-aliases` (SLOP010/SLOP011/SLOP012)**:
  - *Remedy*: Replace untyped `Any`/`object` with explicit `typing.Protocol` interfaces or bounded type parameters (`[T: SupportsProcessing]`).
* **`require-safety-comment-for-type-assertion` (SLOP015)**:
  - *Remedy*: Document the invariant proven elsewhere: `# SAFETY: validated non-empty and parsed by request schema decoder`.

#### Category 2: Dynamic Reflection & Testing Seams

* **`no-module-mocking` (SLOP004)**:
  - *Remedy*: Refactor code to accept dependencies via constructor injection. In tests, supply an in-memory test double conforming to the `Protocol`.
* **`no-reflect-apply` (SLOP006) & `no-reflect-get` (SLOP007)**:
  - *Remedy*: Use direct typed attribute access (`obj.field`), method polymorphism (`obj.execute()`), or structural pattern matching (`match item:`).
* **`no-conditional-empty-object-spread` (SLOP002)**:
  - *Remedy*: Construct dictionaries with explicit updates: `payload = dict(base); if condition: payload.update(extra)`.
* **`no-shape-in-symbol-names` (SLOP009)**:
  - *Remedy*: Name models after the domain entity (`User`, `UserProfile`, `UserRecord`) instead of `UserShape`.

#### Category 3: API Signatures, Error Flow & Control Flow

* **`no-runtime-typeof` (SLOP008)**:
  - *Remedy*: Parse external inputs once at the I/O boundary into validated domain models. Internal classes trust their static type contracts.
* **`no-excessive-parameters` (SLOP016)**:
  - *Remedy*: Group parameters into a dedicated `@dataclass(frozen=True)` options object (`ExportOptions`).
* **`require-keyword-only-booleans` (SLOP017)**:
  - *Remedy*: Make boolean arguments keyword-only: `def process(user_id: str, *, dry_run: bool = False):`.
* **`no-silent-exception-swallow` (SLOP018)**:
  - *Remedy*: Handle specific exceptions, log failures, or chain exceptions: `raise ServiceError(...) from err`.
* **`no-unnamed-tuple-returns` (SLOP019)**:
  - *Remedy*: Return a named `@dataclass(frozen=True)` or `NamedTuple` instead of `tuple[bool, str, int]`.
* **`no-assert-validation` (SLOP020)**:
  - *Remedy*: Replace `assert` with explicit `if condition: raise ValueError(...)`.
* **`no-mutable-default-arguments` (SLOP021)**:
  - *Remedy*: Use `items: list[str] | None = None` and instantiate inside the function, or `field(default_factory=list)`.
