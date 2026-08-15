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

   This creates `tools/anti-slop/`. Pass another relative destination as the first argument when the repository has an established tooling layout. The script refuses to replace an existing destination; only use `--force` after backing up and reviewing existing files.

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

   Keep every existing ignore. Adjust the final pattern when the plugin was copied elsewhere.

4. Run the repository's lint checks:

   ```bash
   python -m anti_slop check
   ```

   If findings appear in owned project source, report them and fix them only when the user asked for migration/cleanup. Do not suppress rules, weaken rule severity, add unsafe casts, or mechanically launder types to make lint pass.

5. Review the final diff and clearly report:
   - copied path,
   - configuration changed,
   - checks run and any findings.
