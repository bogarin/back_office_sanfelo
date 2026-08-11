---
name: django
description: This skill provides preferred code style instructions as well as best practices and common patterns/antipatterns.
---

# Preferred Code Style

- Naming Conventions:
  - Use `snake_case` for variable and function names.
  - Use `PascalCase` for class names.
  - Use `UPPER_SNAKE_CASE` for constants.
- Import statements:
  - use `uv run ruff format --fix` to automatically format imports and code style.
  - Local imports are strictly prohibited. The only exception is to fix circular imports.
  - Use Python 3.14 syntax and constructs. Never use older syntax.
  - Never try to run python scripts directly, always use `uv`.
  - Use of pip and requirements.txt is strictly prohibited.


# Testing

When writing tests:
- Leverage pytest and django-pytest features
- Class-based tests are forbidden. Function-based tests are preferred.
- Try to consolidate repetitive tests as parametrized tests
- Always try to reuse fixtures.

# Quality Gates & Tooling

All commands MUST be executed through `uv`. Never use global python, pip, or manual virtualenv activation.

- **Dependency Management:** Use `uv add <package>` or `uv remove <package>`.
- **Django Management:** Use `uv run manage.py <command>`.
- **Testing:** Use `uv run pytest`.
- **General Execution:** Always prefix python scripts with `uv run`.
- **No requirements.txt:** The use of `requirements.txt` is strictly forbidden. All dependencies must be managed via `pyproject.toml` and `uv.lock`.

## Automated quality gates (prek + ruff + ty + djangofmt)

The project enforces quality through `prek.toml` (18 hooks). Run all hooks manually:

```bash
just pre-commit          # prek run --all-files (all 18 hooks)
```

Or run individual tools:

```bash
just lint                # ruff check (read-only, no autofix)
just format              # ruff check --fix + ruff format
just typecheck           # ty check
just djlint              # djangofmt (Django template formatter)
uv run manage.py check   # manage.py check (framework + custom checks)
just audit-tests         # AST audit of test suite
just test                # pytest
```

### What each tool detects

| Tool | Hook | Detects |
|------|------|---------|
| **ruff** | `ruff check` | Syntax errors (E999), deprecated patterns (UP), security issues (S, BLE), bugbears (B), Django anti-patterns (DJ), unused noqa (RUF100), bare `# noqa` (PGH004) |
| **ruff format** | `ruff-format` | Formatting (single quotes, line-length 100) |
| **ty** | `ty` | Type errors, wrong annotations, missing overrides, unresolved imports |
| **djangofmt** | `djangofmt` | Malformed Django templates (unclosed tags, broken HTML) |
| **pytest collect** | `pytest-collect` (local) | SyntaxErrors in test modules, broken imports, invalid settings |
| **Django check** | `django-check` (local) | Invalid settings + 4 custom project checks (see below) |
| **AST audit** | `audit-tests` (local) | Class-based tests (forbidden), tests without assertions, tautological asserts |
| **builtins** | 10 hooks | Trailing whitespace, EOF, check-toml/yaml/json, merge conflicts, large files, private keys, no-commit-to-branch (main) |

### Custom Django system checks (`apps/core/checks.py`)

Registered via `CoreConfig.ready()`, run by `manage.py check`:

- **`aiph_core.E001`** — SECRET_KEY contains `django-insecure-` marker
- **`aiph_core.W002`** — `ACCOUNT_RATE_LIMITS` (django-allauth) not configured
- **`aiph_core.E010`** — Dead settings removed in modern Django (SECURE_BROWSER_XSS_FILTER, STATICFILES_STORAGE, etc.)
- **`aiph_core.E011`** — Missing `STORAGES` dict (mandatory since Django 4.2)

### AST audit script (`apps/core/scripts/check_tests.py`)

Enforces test-suite rules from this skill:

- **ERROR:** Any `class Test*:` — function-based tests are mandatory
- **WARN:** `def test_*` without `assert` in body
- **ERROR:** Tautological asserts (`assert True`, `assert x == x`)

### Workflow when fixing code

1. Write the fix
2. Run `just format` (ruff autofix + format)
3. Run `just lint` (verify no new ruff errors)
4. Run `uv run manage.py check` (Django system checks pass)
5. Run `just test` (tests pass)
6. Run `just pre-commit` (all 18 hooks green)

Or in one step: `just pre-commit && just test`

### `# noqa` policy

All `# noqa` directives MUST include a rule code (e.g. `# noqa: S308`, not bare `# noqa`). RUF100 (unused noqa) and PGH004 (bare noqa) are enforced. When adding a new `# noqa`, verify it's truly necessary — prefer fixing the underlying issue.

# Agent Behavior & Compliance

- **No Unsolicited Suggestions:** Do not provide alternatives or unsolicited suggestions. Stick strictly to the approved specifications in `docs/` and the decisions in `ADRs`.
- **Strict Compliance:** If a technical detail is not specified, ask for clarification instead of guessing or suggesting a "common practice".
- **Execution First:** Focus on precise implementation of the defined specs.
