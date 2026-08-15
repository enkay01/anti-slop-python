---
name: install-anti-slop
description: Check or install opinionated Python anti-slop lint rules. Supports zero-commit audits via bundled scripts or full repository installation with pyproject.toml configuration.
---

# Anti-Slop (Python)

Opinionated Python lint rules rejecting low-evidence and low-signal patterns.

This skill provides two distinct modes:
1. **Mode 1: Zero-Commit Check (Advisory & Audits)** - Run checks directly against any Python project without modifying its files or committing configuration.
2. **Mode 2: Full Repository Installation (Vendoring & CI)** - Vendor the rules into `tools/anti_slop/` and configure `pyproject.toml` for team enforcement and CI/CD pipelines.

---

## Mode 1: Zero-Commit Check (Advisory & Audits)

Use this mode when reviewing code, checking PRs, or auditing repositories without leaving any untracked files or committing configuration.

### Usage

```bash
# Check the entire repository or a specific path
python <skill-directory>/scripts/check.py [path]

# Example: check src directory with JSON output
python <skill-directory>/scripts/check.py src/ --format json
```

* **Zero Footprint**: Does not modify `pyproject.toml` or create any files in the target repository.
* **Auto-Discovery**: Automatically respects the target project's `pyproject.toml` rules and ignore patterns if present; otherwise applies default strict rules.

---

## Mode 2: Full Repository Installation (Vendoring & CI)

Use this mode when the user requests permanent lint enforcement, pre-commit hooks, or CI integration.

### Procedure

1. Inspect the repository before changing it:
   - Read its agent instructions and `pyproject.toml`.
   - Check `git status` and preserve unrelated changes.
   - Identify the package manager and virtual environment (`uv`, `poetry`, `pip`, etc.).
   - Check whether anti-slop files or rules already exist. Do not overwrite them without reviewing the diff.

2. Copy the bundled plugin from this skill. Run from the target repository:

   ```bash
   python <skill-directory>/scripts/install.py [tools/anti_slop]
   ```

   This creates `tools/anti_slop/`. Pass another relative destination as the first argument when the repository has an established tooling layout. The script refuses to replace an existing destination; only use `--force` after backing up and reviewing existing files.

3. Register the plugin, configure ignores, and enable all rules in `pyproject.toml`:

   ```toml
   [tool.anti-slop]
   ignore_patterns = [
       ".agent/**",
       ".agents/**",
       ".claude/**",
       ".codex/**",
       ".continue/**",
       ".cursor/**",
       ".gemini/**",
       ".git/**",
       ".opencode/**",
       ".pi/**",
       ".roo/**",
       ".venv/**",
       ".windsurf/**",
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
   ```

   Keep every existing ignore. Adjust the final pattern when the plugin was copied elsewhere.

4. Run the repository's lint checks:

   ```bash
   python tools/anti_slop/cli.py check
   ```

   If findings appear in owned project source, report them and fix them only when the user asked for migration/cleanup.

5. Review the final diff and clearly report:
   - copied path,
   - configuration changed,
   - checks run and any findings.

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
