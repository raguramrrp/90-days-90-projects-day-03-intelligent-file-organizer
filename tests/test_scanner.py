"""Unit tests for the filesystem scanner and metadata extraction engine."""

import os
from pathlib import Path
from datetime import datetime
import pytest

from src.scanner import FileScanner, FileInfo, format_bytes


def test_format_bytes() -> None:
    assert format_bytes(0) == "0 B"
    assert format_bytes(512) == "512 B"
    assert format_bytes(1024) == "1 KB"
    assert format_bytes(1536) == "1.50 KB"
    assert format_bytes(1048576) == "1 MB"
    assert format_bytes(1073741824) == "1 GB"


def test_file_scanner_basic(tmp_path: Path) -> None:
    # Setup test directory
    file_a = tmp_path / "document.pdf"
    file_a.write_bytes(b"%PDF-1.4 Mock document")

    file_b = tmp_path / "data.tar.gz"
    file_b.write_bytes(b"\x1f\x8b\x08Mock tar gzip archive")

    scanner = FileScanner()
    files = scanner.scan_directory(tmp_path, recursive=False)

    assert len(files) == 2
    names = {f.name for f in files}
    assert "document.pdf" in names
    assert "data.tar.gz" in names

    tar_info = next(f for f in files if f.name == "data.tar.gz")
    assert tar_info.extension == ".tar.gz"
    assert tar_info.stem == "data"
    assert tar_info.size_bytes == len(b"\x1f\x8b\x08Mock tar gzip archive")


def test_file_scanner_hidden_and_excluded(tmp_path: Path) -> None:
    # Create normal file
    (tmp_path / "normal.txt").write_text("hello")
    # Create dotfile
    (tmp_path / ".hidden_config").write_text("secret")
    # Create desktop.ini
    (tmp_path / "desktop.ini").write_text("[Shell]")

    # Scanner with include_hidden=False
    scanner = FileScanner(include_hidden=False)
    files = scanner.scan_directory(tmp_path, recursive=False)

    names = {f.name for f in files}
    assert "normal.txt" in names
    assert ".hidden_config" not in names
    assert "desktop.ini" not in names

    # Scanner with include_hidden=True
    scanner_hidden = FileScanner(include_hidden=True)
    files_hidden = scanner_hidden.scan_directory(tmp_path, recursive=False)
    names_hidden = {f.name for f in files_hidden}
    assert ".hidden_config" in names_hidden
    # desktop.ini is in COMMON_SYSTEM_FILES so it remains excluded
    assert "desktop.ini" not in names_hidden


def test_file_scanner_recursive(tmp_path: Path) -> None:
    sub = tmp_path / "subdir"
    sub.mkdir()
    (tmp_path / "root_file.txt").write_text("root")
    (sub / "nested_file.txt").write_text("nested")

    scanner = FileScanner()
    shallow_files = scanner.scan_directory(tmp_path, recursive=False)
    assert len(shallow_files) == 1
    assert shallow_files[0].name == "root_file.txt"

    recursive_files = scanner.scan_directory(tmp_path, recursive=True)
    assert len(recursive_files) == 2
    rec_names = {f.name for f in recursive_files}
    assert "root_file.txt" in rec_names
    assert "nested_file.txt" in rec_names
