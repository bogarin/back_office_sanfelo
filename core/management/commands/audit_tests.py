"""AST audit enforcing test-suite rules from the project skill.

Prohibits:
- class-based tests (any class pytest would collect).

Warns on:
- ``def test_*`` without a single assertion in the reachable body.

A ``ClassDef`` is considered a class-based test when **either**:
- its name starts with ``Test`` (aligned with ``python_classes = ['Test*']``
  from ``pyproject.toml``), **or**
- it contains at least one direct ``def test_*`` method.

This leaves legitimate helpers untouched (factories, mocks, fakes, builders,
DTOs, exception classes) as long as they don't follow the test_* convention.

Usage::

    python manage.py audit_tests
    python manage.py audit_tests --paths tests/core
    python manage.py audit_tests --strict
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


@dataclass
class AuditResult:
    """Aggregated findings from the audit walk."""

    failures: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _class_has_test_methods(node: ast.ClassDef) -> bool:
    """True if the class body declares a direct ``def test_*`` method."""
    return any(
        isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
        and child.name.startswith('test_')
        for child in node.body
    )


def _is_class_based_test(node: ast.ClassDef) -> bool:
    """True if pytest would collect this class as a test class.

    Aligned with ``python_classes = ['Test*']`` from ``pyproject.toml``.
    """
    return node.name.startswith('Test') or _class_has_test_methods(node)


def _with_is_assertion(node: ast.With | ast.AsyncWith) -> bool:
    """A ``with`` block acts as an assertion when its context manager is
    ``pytest.raises(...)``, ``pytest.warns(...)``, ``pytest.deprecated_call(...)``,
    or ``self.assertRaises(...)`` / ``self.assertWarns(...)``.
    """
    pytest_assertion_calls = {'raises', 'warns', 'deprecated_call'}
    for item in node.items:
        ctx = item.context_expr
        match ctx:
            case ast.Call(func=ast.Attribute(value=ast.Name(id='pytest'), attr=attr)):
                if attr in pytest_assertion_calls:
                    return True
            case ast.Call(func=ast.Attribute(attr='assertRaises')):
                return True
            case ast.Call(func=ast.Attribute(attr='assertWarns')):
                return True
    return False


def _has_assertion(body: list[ast.stmt]) -> bool:
    """Recursively look for an assertion in the reachable body."""
    for stmt in body:
        if isinstance(stmt, ast.Assert):
            return True
        if isinstance(stmt, (ast.With, ast.AsyncWith)):
            if _with_is_assertion(stmt) or _has_assertion(stmt.body):
                return True
        elif isinstance(stmt, (ast.For, ast.While, ast.If)):
            if _has_assertion(stmt.body) or _has_assertion(stmt.orelse):
                return True
        elif isinstance(stmt, ast.Try):
            for group in (stmt.body, stmt.orelse, stmt.finalbody):
                if _has_assertion(group):
                    return True
    return False


def check_file(path: Path, root: Path) -> tuple[list[str], list[str]]:
    """Audit a single test file. Returns ``(failures, warnings)`` lines."""
    failures: list[str] = []
    warnings: list[str] = []
    rel = path.relative_to(root)

    try:
        source = path.read_text()
    except OSError as exc:
        failures.append(f'{rel}:0: cannot read file: {exc}')
        return failures, warnings

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        failures.append(f'{rel}:{exc.lineno or 0}: SYNTAX ERROR: {exc.msg}')
        return failures, warnings

    for node in ast.walk(tree):
        match node:
            case ast.ClassDef() if _is_class_based_test(node):
                failures.append(
                    f'{rel}:{node.lineno}: ERROR class-based test forbidden '
                    f'(skill requires function-based): class {node.name}'
                )
            case ast.FunctionDef(name=name) as fn if name.startswith(
                'test_'
            ) and not _has_assertion(fn.body):
                warnings.append(f'{rel}:{fn.lineno}: WARN test without assertion: {name}')
            case ast.AsyncFunctionDef(name=name) as fn if name.startswith(
                'test_'
            ) and not _has_assertion(fn.body):
                warnings.append(f'{rel}:{fn.lineno}: WARN test without assertion: {name}')

    return failures, warnings


def audit(root: Path) -> AuditResult:
    """Walk ``root`` for ``test_*.py`` files and return aggregated findings."""
    result = AuditResult()
    for path in sorted(root.rglob('test_*.py')):
        if not path.is_file() or '__pycache__' in path.parts:
            continue
        failures, warnings = check_file(path, root)
        result.failures.extend(failures)
        result.warnings.extend(warnings)
    return result


class Command(BaseCommand):
    """Run an AST audit over the test suite."""

    help = (
        'Audit the test suite for class-based tests (forbidden) and tests '
        'without assertions (warned). Aligned with python_classes = [Test*] '
        'from pyproject.toml. Exits non-zero on ERROR; --strict promotes '
        'WARN to ERROR.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--paths',
            default=str(getattr(settings, 'BASE_DIR', Path.cwd()) / 'tests'),
            help='Root directory to audit (default: <BASE_DIR>/tests).',
        )
        parser.add_argument(
            '--strict',
            action='store_true',
            default=False,
            help='Promote WARN (test without assertion) to ERROR.',
        )

    def handle(self, *args, **options):
        root = Path(options['paths']).resolve()
        strict: bool = options['strict']

        if not root.exists():
            raise CommandError(f'Path does not exist: {root}')
        if not root.is_dir():
            raise CommandError(f'Path is not a directory: {root}')

        result = audit(root)

        if strict:
            result.failures.extend(result.warnings)
            result.warnings = []

        for msg in result.failures:
            self.stderr.write(self.style.ERROR(msg))
        for msg in result.warnings:
            self.stderr.write(self.style.WARNING(msg))

        if result.failures:
            summary = f'{len(result.failures)} error(s), {len(result.warnings)} warning(s)'
            raise CommandError(summary)

        if result.warnings:
            self.stdout.write(self.style.WARNING(f'0 errors, {len(result.warnings)} warning(s)'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Audit passed: {root}'))
