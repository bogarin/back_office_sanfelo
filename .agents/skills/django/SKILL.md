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
  
