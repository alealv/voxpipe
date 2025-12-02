"""Tests for the CLI."""

from __future__ import annotations

from typer.testing import CliRunner

from voxpipe import app
from voxpipe._internal import debug

runner = CliRunner()


def test_main_no_args() -> None:
    """CLI with no args shows help (exit code 2 is expected for no_args_is_help)."""
    result = runner.invoke(app)
    assert result.exit_code == 2  # typer returns 2 for missing required args
    assert "usage" in result.output.lower()


def test_show_help() -> None:
    """Show help."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "voxpipe" in result.output.lower()


def test_show_version() -> None:
    """Show version."""
    result = runner.invoke(app, ["-V"])
    assert result.exit_code == 0
    assert debug._get_version() in result.output


def test_show_debug_info() -> None:
    """Show debug information."""
    result = runner.invoke(app, ["--debug-info"])
    assert result.exit_code == 0
    output = result.output.lower()
    assert "python" in output
    assert "system" in output


def test_subcommands_exist() -> None:
    """All expected subcommands are registered."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for cmd in ["extract", "transcribe", "diarize", "merge", "correct", "translate", "export", "pipeline"]:
        assert cmd in result.output
