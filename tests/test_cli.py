"""Integration tests for CLI interface commands, flags, and outputs."""

import subprocess
import sys
from pathlib import Path
import pytest


def run_organizer_cli(*args: str) -> subprocess.CompletedProcess:
    """Helper to execute the main script via subprocess."""
    cmd = [sys.executable, "src/main.py", *args]
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent,
    )


def test_cli_help() -> None:
    res = run_organizer_cli("--help")
    assert res.returncode == 0
    assert "Context-Aware Desktop File Organization Automation Engine" in res.stdout
    assert "--dry-run" in res.stdout
    assert "--organize" in res.stdout
    assert "--date-grouping" in res.stdout


def test_cli_stats() -> None:
    res = run_organizer_cli("--stats")
    assert res.returncode == 0
    assert "CONTEXT-AWARE FILE ORGANIZER - SYSTEM METRICS" in res.stdout
    assert "Total Batches Recorded" in res.stdout


def test_cli_list_rules() -> None:
    res = run_organizer_cli("--list-rules")
    assert res.returncode == 0
    assert "CONFIGURED ORGANIZATION RULES" in res.stdout
    assert "Screenshots" in res.stdout


def test_cli_dry_run_on_temp_dir(tmp_path: Path) -> None:
    # Create test files
    (tmp_path / "sample.pdf").write_text("dummy")
    (tmp_path / "photo.jpg").write_text("image")

    res = run_organizer_cli("--dry-run", str(tmp_path))
    assert res.returncode == 0
    assert "SIMULATION & SCAN" in res.stdout
    assert "Discovered Files : 2" in res.stdout
    assert "[DRY RUN COMPLETE] No files were modified on disk." in res.stdout
    # Verify files were NOT moved
    assert (tmp_path / "sample.pdf").exists()
    assert (tmp_path / "photo.jpg").exists()
