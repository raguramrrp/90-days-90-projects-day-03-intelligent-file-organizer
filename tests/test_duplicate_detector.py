"""Unit tests for file hashing, size grouping, and duplicate cluster detection."""

from pathlib import Path
from datetime import datetime, timedelta
import pytest

from src.scanner import FileScanner
from src.duplicates import DuplicateDetector, DuplicateStrategy


def test_duplicate_detector_exact_matches(tmp_path: Path) -> None:
    # Create identical files
    content = b"Exact identical binary content for duplicate checking"
    f1 = tmp_path / "original.pdf"
    f2 = tmp_path / "copy.pdf"
    f3 = tmp_path / "another_copy.pdf"

    f1.write_bytes(content)
    f2.write_bytes(content)
    f3.write_bytes(content)

    # Create unique file with different size
    f_unique = tmp_path / "unique.txt"
    f_unique.write_bytes(b"Distinct content")

    # Create file with same size as f1 but different bytes
    f_same_size = tmp_path / "same_size_diff_bytes.pdf"
    f_same_size.write_bytes(b"X" * len(content))

    scanner = FileScanner()
    files = scanner.scan_directory(tmp_path)

    detector = DuplicateDetector()
    report = detector.detect_duplicates(files)

    assert len(report.groups) == 1
    group = report.groups[0]
    assert group.size_bytes == len(content)
    assert group.total_copies == 3
    assert len(group.duplicate_files) == 2
    assert report.total_duplicates == 2
    assert report.total_wasted_bytes == len(content) * 2

    # Check hash lookup
    assert f1 in report.hash_lookup
    assert f2 in report.hash_lookup
    assert f3 in report.hash_lookup
    assert report.hash_lookup[f1] == report.hash_lookup[f2]
    assert report.hash_lookup[f1] != report.hash_lookup[f_same_size]


def test_duplicate_detector_no_duplicates(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_bytes(b"one")
    (tmp_path / "b.txt").write_bytes(b"two bytes")
    (tmp_path / "c.txt").write_bytes(b"three bytes more")

    scanner = FileScanner()
    files = scanner.scan_directory(tmp_path)

    detector = DuplicateDetector()
    report = detector.detect_duplicates(files)

    assert len(report.groups) == 0
    assert report.total_duplicates == 0
    assert report.total_wasted_bytes == 0
