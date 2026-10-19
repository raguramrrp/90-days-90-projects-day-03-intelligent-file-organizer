"""File classifier module for grouping files by extension category and temporal attributes."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set
from src.scanner import FileInfo


class DateGroupingMode(str, Enum):
    """Supported temporal clustering modes for organized files."""
    NONE = "none"
    YEAR = "year"                  # 2026
    YEAR_MONTH = "year_month"      # 2026-10
    FULL_DATE = "full_date"        # 2026-10-19


class HierarchyStyle(str, Enum):
    """Directory tree layout strategy."""
    CATEGORY_FIRST = "category_first"  # Documents/2026-10/
    DATE_FIRST = "date_first"          # 2026-10/Documents/
    CATEGORY_ONLY = "category_only"    # Documents/


class FileClassifier:
    """Classifies files into semantic categories and generates hierarchical folder paths."""

    DEFAULT_EXT_MAP: Dict[str, List[str]] = {
        "Documents": [
            ".pdf", ".docx", ".doc", ".txt", ".rtf", ".odt", ".epub",
            ".md", ".tex", ".pages", ".wpd", ".log"
        ],
        "Images": [
            ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp",
            ".tiff", ".tif", ".ico", ".raw", ".cr2", ".nef", ".heic", ".psd"
        ],
        "Audio": [
            ".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a", ".wma",
            ".mid", ".midi", ".aif", ".aiff"
        ],
        "Video": [
            ".mp4", ".mkv", ".mov", ".avi", ".webm", ".wmv", ".flv",
            ".m4v", ".3gp", ".ts", ".vob"
        ],
        "Archives": [
            ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz",
            ".tar.gz", ".tar.bz2", ".tar.xz", ".iso", ".tgz", ".cab"
        ],
        "Code & Scripts": [
            ".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".htm",
            ".css", ".scss", ".json", ".xml", ".sql", ".java", ".c",
            ".cpp", ".h", ".hpp", ".cs", ".go", ".rs", ".php", ".rb",
            ".sh", ".bat", ".ps1", ".cmd", ".yaml", ".yml", ".toml", ".ini"
        ],
        "Spreadsheets & Data": [
            ".xlsx", ".xls", ".csv", ".tsv", ".parquet", ".feather",
            ".jsonl", ".sqlite", ".db", ".mdb", ".accdb", ".ods"
        ],
        "Executables & Installers": [
            ".exe", ".msi", ".apk", ".dmg", ".pkg", ".appimage", ".deb", ".rpm"
        ],
        "Presentations": [
            ".pptx", ".ppt", ".key", ".odp"
        ]
    }

    CATEGORY_ICONS: Dict[str, str] = {
        "Documents": "📄",
        "Images": "🖼️",
        "Audio": "🎵",
        "Video": "🎬",
        "Archives": "📦",
        "Code & Scripts": "💻",
        "Spreadsheets & Data": "📊",
        "Executables & Installers": "⚙️",
        "Presentations": "📽️",
        "Miscellaneous": "📁",
    }

    def __init__(self, custom_mapping: Optional[Dict[str, List[str]]] = None) -> None:
        self.category_mapping = custom_mapping or dict(self.DEFAULT_EXT_MAP)
        self._reverse_map: Dict[str, str] = {}
        self._rebuild_reverse_index()

    def _rebuild_reverse_index(self) -> None:
        """Build extension-to-category lookup table for O(1) classification."""
        self._reverse_map.clear()
        for category, extensions in self.category_mapping.items():
            for ext in extensions:
                self._reverse_map[ext.lower()] = category

    def get_category(self, file_info: FileInfo) -> str:
        """Determine semantic category for a given file info object."""
        ext = file_info.extension.lower()
        return self._reverse_map.get(ext, "Miscellaneous")

    def get_icon_for_category(self, category: str) -> str:
        """Return visual emoji/icon symbol representing the category."""
        return self.CATEGORY_ICONS.get(category, "📁")

    def format_date_segment(self, file_info: FileInfo, mode: DateGroupingMode) -> Optional[str]:
        """Generate relative date directory segment based on modified timestamp."""
        dt = file_info.modified_at
        if mode == DateGroupingMode.YEAR:
            return dt.strftime("%Y")
        elif mode == DateGroupingMode.YEAR_MONTH:
            return dt.strftime("%Y-%m")
        elif mode == DateGroupingMode.FULL_DATE:
            return dt.strftime("%Y-%m-%d")
        return None

    def compute_destination_folder(
        self,
        file_info: FileInfo,
        date_mode: DateGroupingMode = DateGroupingMode.NONE,
        hierarchy: HierarchyStyle = HierarchyStyle.CATEGORY_FIRST,
    ) -> Path:
        """Compute relative folder path where file should be organized.
        
        Examples:
            - Documents/
            - Documents/2026-10/
            - 2026-10/Documents/
        """
        category = self.get_category(file_info)
        date_segment = self.format_date_segment(file_info, date_mode)

        if not date_segment or hierarchy == HierarchyStyle.CATEGORY_ONLY or date_mode == DateGroupingMode.NONE:
            return Path(category)

        if hierarchy == HierarchyStyle.CATEGORY_FIRST:
            return Path(category) / date_segment
        elif hierarchy == HierarchyStyle.DATE_FIRST:
            return Path(date_segment) / category

        return Path(category)
