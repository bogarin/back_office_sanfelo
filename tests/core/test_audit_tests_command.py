"""Tests for the ``audit_tests`` management command.

Covers:
- Detection of class-based tests by name (``Test*``).
- Detection of class-based tests by presence of ``def test_*`` methods.
- Allowlist of legitimate helpers (factories, mocks, fakes).
- Warning path for ``def test_*`` without assertions.
- ``--strict`` promotion of warnings to errors.
- Output format (``path:line`` clickable).
- ``pytest.raises`` recognised as an assertion.

These tests themselves are function-based, exemplifying the project skill.
"""

import io
from pathlib import Path

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError


def _write_test_file(directory: Path, name: str, content: str) -> Path:
    path = directory / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path


def test_command_detects_class_with_test_prefix(tmp_path):
    _write_test_file(tmp_path, 'test_foo.py', 'class TestFoo:\n    pass\n')
    with pytest.raises(CommandError, match='1 error'):
        call_command('audit_tests', paths=str(tmp_path))


def test_command_detects_class_with_test_method_even_without_prefix(tmp_path):
    _write_test_file(
        tmp_path,
        'test_foo.py',
        'class FooGrouping:\n    def test_x(self):\n        assert True\n',
    )
    with pytest.raises(CommandError, match='1 error'):
        call_command('audit_tests', paths=str(tmp_path))


def test_command_allows_helper_class_without_test_methods(tmp_path):
    _write_test_file(
        tmp_path,
        'test_foo.py',
        'class MockAuthBackend:\n    def authenticate(self, request):\n        return None\n',
    )
    call_command('audit_tests', paths=str(tmp_path))


def test_command_allows_factory_class(tmp_path):
    _write_test_file(
        tmp_path,
        'test_foo.py',
        'class UserFactory:\n    def build(self, **kwargs):\n        return kwargs\n',
    )
    call_command('audit_tests', paths=str(tmp_path))


def test_command_allows_fake_client_class(tmp_path):
    _write_test_file(
        tmp_path,
        'test_foo.py',
        'class FakeHttpClient:\n    def get(self, url):\n        return 200\n',
    )
    call_command('audit_tests', paths=str(tmp_path))


def test_command_warns_on_test_without_assert(tmp_path):
    _write_test_file(
        tmp_path,
        'test_foo.py',
        'def test_does_nothing():\n    x = 1\n',
    )
    out = io.StringIO()
    call_command('audit_tests', paths=str(tmp_path), stdout=out)
    assert '0 errors, 1 warning' in out.getvalue()


def test_command_strict_promotes_warning_to_error(tmp_path):
    _write_test_file(
        tmp_path,
        'test_foo.py',
        'def test_does_nothing():\n    x = 1\n',
    )
    with pytest.raises(CommandError):
        call_command('audit_tests', paths=str(tmp_path), strict=True)


def test_command_reports_file_and_line(tmp_path):
    _write_test_file(
        tmp_path,
        'test_foo.py',
        '\n\nclass TestFoo:\n    pass\n',
    )
    err = io.StringIO()
    with pytest.raises(CommandError):
        call_command('audit_tests', paths=str(tmp_path), stderr=err)
    output = err.getvalue()
    assert 'test_foo.py:3' in output
    assert 'TestFoo' in output


def test_command_clean_on_function_based_test(tmp_path):
    _write_test_file(
        tmp_path,
        'test_foo.py',
        'def test_passes():\n    assert 1 + 1 == 2\n',
    )
    out = io.StringIO()
    call_command('audit_tests', paths=str(tmp_path), stdout=out)
    assert 'Audit passed' in out.getvalue()


def test_command_raises_on_nonexistent_path():
    with pytest.raises(CommandError, match='does not exist'):
        call_command('audit_tests', paths='/nonexistent/path/xyz/abc')


def test_command_recognises_pytest_raises_as_assertion(tmp_path):
    _write_test_file(
        tmp_path,
        'test_foo.py',
        'import pytest\n'
        'def test_raises():\n'
        '    with pytest.raises(ValueError):\n'
        '        raise ValueError()\n',
    )
    call_command('audit_tests', paths=str(tmp_path))


def test_command_recognises_self_assert_raises_as_assertion(tmp_path):
    _write_test_file(
        tmp_path,
        'test_foo.py',
        'from unittest import TestCase\n'
        'def test_asserts(self):\n'
        '    with TestCase().assertRaises(KeyError):\n'
        '        raise KeyError()\n',
    )
    call_command('audit_tests', paths=str(tmp_path))


def test_command_skips_pycache(tmp_path):
    _write_test_file(
        tmp_path,
        'test_clean.py',
        'def test_ok():\n    assert True\n',
    )
    _write_test_file(
        tmp_path / '__pycache__',
        'test_cached.py',
        'class TestShouldBeIgnored:\n    pass\n',
    )
    call_command('audit_tests', paths=str(tmp_path))
