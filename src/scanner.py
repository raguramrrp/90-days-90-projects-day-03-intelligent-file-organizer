"""File scanner module for discovering and profiling local filesystem artifacts."""

from __future__ import annotations

import os
import sys
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Set, List

logger = logging.getLogger(__name__)


def format_bytes(size_bytes: int) -> str:
    """Format an integer byte count into human-readable binary unit notation."""
    if size_bytes <= 0:
        return "0 B"
    if size_bytes < 1024:
        return f"{size_bytes} B"
    units = ["KB", "MB", "GB", "TB", "PB"]
    size = float(size_bytes)
    for unit in units:
        size /= 1024.0
        if size < 1024.0 or unit == units[-1]:
            if size.is_integer():
                return f"{int(size)} {unit}"
            return f"{size:.2f} {unit}"
    return f"{size_bytes} B"


@dataclass(frozen=True)
class FileInfo:
    """Immutable metadata representation of a single scanned filesystem entry."""
    path: Path
    name: str
    stem: str
    extension: str
    size_bytes: int
    created_at: datetime
    modified_at: datetime
    is_hidden: bool
    is_symlink: bool

    @property
    def readable_size(self) -> str:
        """Return human-readable file size string."""
        return format_bytes(self.size_bytes)

    @property
    def modified_iso(self) -> str:
        """Return ISO-formatted modification timestamp."""
        return self.modified_at.strftime("%Y-%m-%d %H:%M:%S")


class FileScanner:
    """High-performance directory scanner with metadata extraction and safety guards."""

    COMMON_SYSTEM_FILES: Set[str] = {
        "desktop.ini",
        "thumbs.db",
        ".ds_store",
        "file_organizer.db",
        "file_organizer.db-wal",
        "file_organizer.db-shm",
    }

    COMPOUND_EXTENSIONS: Set[str] = {
        ".tar.gz",
        ".tar.bz2",
        ".tar.xz",
        ".user.js",
    }

    def __init__(
        self,
        include_hidden: bool = False,
        exclude_names: Optional[Set[str]] = None,
        exclude_dirs: Optional[Set[str]] = None,
    ) -> None:
        self.include_hidden = include_hidden
        self.exclude_names = set(exclude_names or set()) | {f.lower() for f in self.COMMON_SYSTEM_FILES}
        self.exclude_dirs = set(exclude_dirs or set())

    @staticmethod
    def get_default_downloads_folder() -> Path:
        """Resolve the current user's default Downloads directory across platforms."""
        downloads = Path.home() / "Downloads"
        if downloads.exists() and downloads.is_dir():
            return downloads
        return Path.home()

    def _extract_extension(self, path: Path) -> str:
        """Extract file extension, prioritizing compound extensions like .tar.gz."""
        lower_name = path.name.lower()
        for compound in self.COMPOUND_EXTENSIONS:
            if lower_name.endswith(compound):
                return compound
        suffix = path.suffix.lower()
        return suffix if suffix else ""

    def _is_hidden(self, path: Path) -> bool:
        """Check whether a file or directory has hidden attributes."""
        if path.name.startswith("."):
            return True
        if sys.platform == "win32":
            try:
                import ctypes
                attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))
                if attrs != -1 and bool(attrs & 2):  # FILE_ATTRIBUTE_HIDDEN = 0x2
                    return True
            except Exception:
                pass
        return False

    def scan_file(self, file_path: Path) -> Optional[FileInfo]:
        """Inspect and return metadata for a single file path."""
        try:
            resolved = file_path.resolve()
            if not resolved.is_file():
                return None

            lower_name = resolved.name.lower()
            if lower_name in self.exclude_names:
                return None

            is_hidden = self._is_hidden(resolved)
            if is_hidden and not self.include_hidden:
                return None

            stat_result = resolved.stat()
            # Windows ctime is creation time, on Unix ctime is metadata change time
            created_ts = getattr(stat_result, "st_birthtime", stat_result.st_ctime)
            created_at = datetime.fromtimestamp(created_ts)
            modified_at = datetime.fromtimestamp(stat_result.st_mtime)

            extension = self._extract_extension(resolved)
            stem = resolved.name[:-len(extension)] if extension else resolved.stem

            return FileInfo(
                path=resolved,
                name=resolved.name,
                stem=stem,
                extension=extension,
                size_bytes=stat_result.st_size,
                created_at=created_at,
                modified_at=modified_at,
                is_hidden=is_hidden,
                is_symlink=resolved.is_symlink(),
            )
        except (PermissionError, FileNotFoundError, OSError) as exc:
            logger.warning("Could not read file metadata for %s: %s", file_path, exc)
            return None

    def scan_directory(
        self,
        directory: Path | str,
        recursive: bool = False,
    ) -> List[FileInfo]:
        """Scan a target directory and return metadata for all eligible files.
        
        Args:
            directory: Path or string path of directory to scan.
            recursive: If True, recursively traverse subdirectories.
            
        Returns:
            List of FileInfo objects sorted by name.
        """
        root = Path(directory).resolve()
        if not root.exists() or not root.is_dir():
            raise ValueError(f"Target directory does not exist or is not a directory: {root}")

        scanned_files: List[FileInfo] = []

        try:
            if recursive:
                for current_dir, dir_names, file_names in os.walk(root):
                    curr_path = Path(current_dir)
                    # Filter out excluded directory names in-place
                    dir_names[:] = [
                        d for d in dir_names
                        if d.lower() not in self.exclude_dirs and (self.include_hidden or not d.startswith("."))
                    ]
                    for fname in file_names:
                        fpath = curr_path / fname
                        info = self.scan_file(fpath)
                        if info is not None:
                            scanned_files.append(info)
            else:
                for entry in os.scandir(root):
                    if entry.is_file(follow_symlinks=False):
                        info = self.scan_file(Path(entry.path))
                        if info is not None:
                            scanned_files.append(info)
        except PermissionError as exc:
            logger.error("Permission denied when accessing directory %s: %s", root, exc)
            raise

        scanned_files.sort(key=lambda f: f.name.lower())
        return scanned_files
