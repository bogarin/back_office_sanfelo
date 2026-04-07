---
name: preferred-commands
description: Preferred commands to use on this project
---

Order of preference

- Recipes in `justfile` if available
  - `just install`
  - `just createsuperuser`
  - `just lint`
  - `just lint-fix *ARGS`
  - `just format *ARGS`
  - `just test APP` 
- `uv` package manager. Use uv to invoke installed utilities or python scripts. DO NOT USE system python.
