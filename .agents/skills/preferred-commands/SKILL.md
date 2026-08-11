---
name: preferred-commands
description: Preferred commands to use on this project
---

Order of preference

- Recipes in `justfile` if available
  - `just install`
  - `just lint`
  - `just format *ARGS`
  - `just test *ARGS`
- `uv` package manager. Use uv to invoke installed utilities or python scripts. DO NOT USE system python.
  - `uv run manage.py createsuperuser` (no `just` recipe for superuser creation)
