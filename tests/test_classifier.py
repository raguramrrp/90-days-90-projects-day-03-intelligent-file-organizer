"""Unit tests for file classification and temporal folder path generation."""

from pathlib import Path
from datetime import datetime
import pytest

from src.scanner import FileInfo
from src.classifier import FileClassifier, DateGroupingMode, HierarchyStyle


@pytest.fixture
def sample_file() -> FileInfo:
    return FileInfo(
        path=Path("/fake/downloads/report.pdf"),
        name="report.pdf",
        stem="report",
        extension=".pdf",
        size_bytes=2048,
        created_at=datetime(2026, 10, 15, 10, 30, 0),
        modified_at=datetime(2026, 10, 19, 14, 0, 0),
        is_hidden=False,
        is_symlink=False,
    )


def test_classifier_category_mapping(sample_file: FileInfo) -> None:
    classifier = FileClassifier()
    assert classifier.get_category(sample_file) == "Documents"
    assert classifier.get_icon_for_category("Documents") == "📄"

    # Test other extension types
    img_file = FileInfo(
        path=Path("/fake/img.png"),
        name="img.png",
        stem="img",
        extension=".png",
        size_bytes=100,
        created_at=datetime.now(),
        modified_at=datetime.now(),
        is_hidden=False,
        is_symlink=False,
    )
    assert classifier.get_category(img_file) == "Images"

    code_file = FileInfo(
        path=Path("/fake/app.py"),
        name="app.py",
        stem="app",
        extension=".py",
        size_bytes=100,
        created_at=datetime.now(),
        modified_at=datetime.now(),
        is_hidden=False,
        is_symlink=False,
    )
    assert classifier.get_category(code_file) == "Code & Scripts"

    unknown_file = FileInfo(
        path=Path("/fake/strange.xyz99"),
        name="strange.xyz99",
        stem="strange",
        extension=".xyz99",
        size_bytes=100,
        created_at=datetime.now(),
        modified_at=datetime.now(),
        is_hidden=False,
        is_symlink=False,
    )
    assert classifier.get_category(unknown_file) == "Miscellaneous"


def test_classifier_temporal_grouping(sample_file: FileInfo) -> None:
    classifier = FileClassifier()

    # None
    folder_none = classifier.compute_destination_folder(sample_file, DateGroupingMode.NONE)
    assert folder_none == Path("Documents")

    # Year
    folder_year = classifier.compute_destination_folder(sample_file, DateGroupingMode.YEAR)
    assert folder_year == Path("Documents/2026")

    # Year-Month
    folder_ym = classifier.compute_destination_folder(sample_file, DateGroupingMode.YEAR_MONTH)
    assert folder_ym == Path("Documents/2026-10")

    # Full Date
    folder_date = classifier.compute_destination_folder(sample_file, DateGroupingMode.FULL_DATE)
    assert folder_date == Path("Documents/2026-10-19")


def test_classifier_hierarchy_styles(sample_file: FileInfo) -> None:
    classifier = FileClassifier()

    # Category First
    dest_cat = classifier.compute_destination_folder(
        sample_file,
        date_mode=DateGroupingMode.YEAR_MONTH,
        hierarchy=HierarchyStyle.CATEGORY_FIRST,
    )
    assert dest_cat == Path("Documents/2026-10")

    # Date First
    dest_date = classifier.compute_destination_folder(
        sample_file,
        date_mode=DateGroupingMode.YEAR_MONTH,
        hierarchy=HierarchyStyle.DATE_FIRST,
    )
    assert dest_date == Path("2026-10/Documents")

    # Category Only
    dest_only = classifier.compute_destination_folder(
        sample_file,
        date_mode=DateGroupingMode.YEAR_MONTH,
        hierarchy=HierarchyStyle.CATEGORY_ONLY,
    )
    assert dest_only == Path("Documents")
