---
name: anti-slop
description: Run opinionated Python anti-slop code quality checks on a repository directly from this skill. Use to audit code quality, check PRs, or enforce clean typing and architecture standards without modifying or polluting the target repository.
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

If a project wants to customize rule severities, configure boundary modules, or add custom ignore patterns, add a `[tool.anti-slop]` section to `pyproject.toml`:

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
"no-tautological-assert" = "error"
"no-assertionless-test" = "error"
"no-silent-test-except" = "error"
"no-opaque-test-names" = "error"
"no-test-sleep" = "error"
"no-test-print" = "error"
"no-private-member-test-access" = "error"
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
* **DO NOT write tautological assertions or line-hitter tests**: `assert True`, `assert x == x`, or assertionless test functions are flagged (SLOP024/SLOP025). Assert concrete domain outputs.
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

#### Category 4: Test Architecture & Verification Quality

* **`no-tautological-assert` (SLOP024)**:
  - *Remedy*: Remove `assert True`, `assert 1`, `assert x == x`, or literal non-empty collection asserts. Assert dynamic, computed outputs against expected values.
* **`no-assertionless-test` (SLOP025)**:
  - *Remedy*: Eliminate line-hitter tests that execute code without asserting. Add explicit domain assertions or `with pytest.raises(...)`.
* **`no-silent-test-except` (SLOP026)**:
  - *Remedy*: Replace `try...except` exception catching in tests with `with pytest.raises(ExpectedError):`. Allow unexpected errors to fail naturally to preserve full tracebacks.
* **`no-opaque-test-names` (SLOP027)**:
  - *Remedy*: Replace generic names (`test1`, `test_case_1`, `test_works`, `test_it`) with descriptive scenario names (e.g. `test_rejects_expired_session_token`).
* **`no-test-sleep` (SLOP028)**:
  - *Remedy*: Eliminate `time.sleep()` and `asyncio.sleep()` in test suites. Use polling loops, condition variables, or fake clock fixtures (`freezegun` / `time_machine`).
* **`no-test-print` (SLOP029)**:
  - *Remedy*: Remove debugging `print()` and `sys.stdout.write()` calls from tests. If testing terminal output, use pytest's `capsys` / `caplog` fixtures.
* **`no-private-member-test-access` (SLOP030)**:
  - *Remedy*: Stop testing private fields (`sut._internal_state`). Verify behavior strictly through the public API or constructor-injected protocols.

---

### Additional Agent Review Heuristics (Offloaded Checks)

When performing code reviews or architecture audits, coding agents should enforce these high-level heuristics:

1. **Free Ride (Piggybacking)**:
   - *Heuristic*: A test function should test a single concept or behavior. If a test chains multiple distinct Act-Assert cycles (`Act 1 -> Assert 1 -> Act 2 -> Assert 2 -> Act 3 -> Assert 3`), split them into independent, focused test functions.
2. **Nitpicker (Monolithic Output Matching)**:
   - *Heuristic*: Avoid asserting against giant multiline JSON, HTML, or dict blobs when only 1 or 2 fields matter. Assert specific domain fields (`assert response.json()["status"] == "active"`) to prevent test brittleness across unrelated schema changes.
3. **Happy Path Only (Missing Boundaries)**:
   - *Heuristic*: Every domain behavior must have negative, edge-case, and boundary test cases (e.g., empty collections, invalid inputs, constraint violations, expired tokens, unauthorized callers).
4. **Cuckoo / Stranger (Test Module Cohesion)**:
   - *Heuristic*: Ensure test files only test units matching their module scope (e.g., `test_order_service.py` must test `OrderService` or its direct contracts, not unrelated domains like `UserProfileManager`). Move foreign tests to their own dedicated test files.

