---
name: install-anti-slop
description: Install and configure the anti-slop Python lint rules in a local Python repository. Use whenever a user asks to add anti-slop lint rules, copy the anti-slop plugin, configure opinionated Python lint rules, or migrate an existing local anti-slop setup.
---

# Install anti-slop

Install the bundled Python anti-slop rules into the current repository and integrate them with the repository's existing lint setup. Preserve unrelated work and adapt to the project's package manager and configuration style.

## Procedure

1. Inspect the repository before changing it:
   - Read its agent instructions and `pyproject.toml`.
   - Check `git status` and preserve unrelated changes.
   - Identify the package manager and virtual environment (`uv`, `poetry`, `pip`, etc.).
   - Check whether anti-slop files or rules already exist. Do not overwrite them without reviewing the diff.

2. Copy the bundled plugin from this skill. Run from the target repository:

   ```bash
   python <skill-directory>/scripts/install.py
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
* **DO NOT suppress rules**: Do not add `# noqa`, `# type: ignore`, or mechanically weaken rule severities to make checks pass without fixing the underlying design.
* **DO NOT add unsafe casts**: Do not wrap raw types in unvalidated `cast()` calls just to silence errors.

---

### Idiomatic Remediation by Rule

#### 1. `no-runtime-typeof` (SLOP008)
* **Problem**: Scattered `type(x) is T` or `isinstance(x, T)` checks in domain models or internal business logic indicate that untrusted data was not parsed at its entry point.
* **Remedy**:
  - Parse external input (JSON payloads, API responses, CLI inputs, raw DB rows) **once at the I/O boundary** into validated domain models or branded value objects using schema parsers (such as Pydantic, msgspec, or dedicated boundary decoder functions).
  - Internal functions and dataclasses should trust their static type contracts and avoid defensive runtime checks.
  - If a function is an intentional predicate guard, annotate its return type with `TypeGuard[T]` or `TypeIs[T]` and enable `allow_in_type_guards = true`.

#### 2. `no-excessive-parameters` (SLOP016)
* **Problem**: Functions with >4 parameters increase cognitive load and argument swapping bugs.
* **Remedy**: Group related parameters into a dedicated `@dataclass(frozen=True)` or Pydantic options object (e.g., `ExportOptions`, `QueryFilters`).

#### 3. `require-keyword-only-booleans` (SLOP017)
* **Problem**: Positional boolean arguments like `process(True, False)` obscure call-site meaning (the "boolean trap").
* **Remedy**: Add `*,` before boolean arguments in the signature: `def process(user_id: str, *, dry_run: bool = False, notify: bool = True):`.

#### 4. `no-silent-exception-swallow` (SLOP018)
* **Problem**: `except Exception: pass` hides bugs and unchained `raise Error` erases root cause tracebacks.
* **Remedy**: Catch specific exception types, log failures, or chain the cause explicitly with `raise ServiceError(...) from err`. Use `contextlib.suppress(FileNotFoundError)` for genuinely benign errors.

#### 5. `no-unnamed-tuple-returns` (SLOP019)
* **Problem**: Returning heterogeneous tuples like `tuple[bool, str, int]` forces brittle positional unpacking.
* **Remedy**: Return a named domain result: `@dataclass(frozen=True) class OperationResult: ...` or `typing.NamedTuple`.

#### 6. `no-assert-validation` (SLOP020)
* **Problem**: `assert` statements vanish in production when running under `python -O`.
* **Remedy**: Replace `assert` with explicit control flow: `if invalid_condition: raise ValueError("...")`. Keep `assert` only in test files.

#### 7. `no-mutable-default-arguments` (SLOP021)
* **Problem**: `def f(items=[])` shares a single mutable list instance across all calls.
* **Remedy**: Use `items: list[str] | None = None` and instantiate inside the function: `items = list(items) if items is not None else []`. For dataclasses/models, use `field(default_factory=list)`.
