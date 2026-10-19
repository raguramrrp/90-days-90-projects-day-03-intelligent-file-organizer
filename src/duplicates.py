"""Duplicate detection module leveraging two-tier file size and cryptographic hashing."""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Callable
from src.scanner import FileInfo, format_bytes

logger = logging.getLogger(__name__)


class DuplicateStrategy(str, Enum):
    """Actions applied to detected duplicate files during organization."""
    REPORT_ONLY = "report_only"      # Identify in UI/logs, organize to normal target
    QUARANTINE = "quarantine"        # Divert duplicates to dedicated '_Duplicates/' directory
    SKIP = "skip"                    # Exclude duplicate files from moving


@dataclass
class DuplicateGroup:
    """A cluster of identical files sharing the exact same cryptographic hash."""
    file_hash: str
    size_bytes: int
    primary_file: FileInfo
    duplicate_files: List[FileInfo] = field(default_factory=list)

    @property
    def total_copies(self) -> int:
        """Total number of file instances in this duplicate cluster."""
        return 1 + len(self.duplicate_files)

    @property
    def wasted_bytes(self) -> int:
        """Space wasted by redundant copies."""
        return self.size_bytes * len(self.duplicate_files)

    @property
    def readable_wasted_space(self) -> str:
        """Human readable wasted disk space."""
        return format_bytes(self.wasted_bytes)


@dataclass
class DuplicateReport:
    """Consolidated summary of duplicate detection across a scanned dataset."""
    groups: List[DuplicateGroup] = field(default_factory=list)
    hash_lookup: Dict[Path, str] = field(default_factory=dict)
    duplicate_paths: Dict[Path, DuplicateGroup] = field(default_factory=dict)

    @property
    def total_duplicates(self) -> int:
        """Number of redundant files identified (excluding primaries)."""
        return sum(len(g.duplicate_files) for g in self.groups)

    @property
    def total_wasted_bytes(self) -> int:
        """Cumulative wasted disk space in bytes."""
        return sum(g.wasted_bytes for g in self.groups)

    @property
    def readable_wasted_space(self) -> str:
        """Formatted cumulative wasted space."""
        return format_bytes(self.total_wasted_bytes)


class DuplicateDetector:
    """High-throughput duplicate detector using streaming SHA-256 with size pre-filtering."""

    def __init__(self, chunk_size: int = 1048576) -> None:
        self.chunk_size = chunk_size  # 1MB buffer for high-throughput disk reads

    def compute_file_hash(self, file_path: Path, algorithm: str = "sha256") -> Optional[str]:
        """Compute cryptographic hash of a file using buffered streaming reads."""
        hasher = hashlib.new(algorithm)
        try:
            with open(file_path, "rb") as f:
                while chunk := f.read(self.chunk_size):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except (PermissionError, FileNotFoundError, OSError) as exc:
            logger.warning("Failed to compute hash for %s: %s", file_path, exc)
            return None

    def detect_duplicates(
        self,
        files: List[FileInfo],
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> DuplicateReport:
        """Analyze a list of scanned files and return clusters of identical files.
        
        Optimization strategy:
        1. Fast O(N) grouping by exact file size. Files with unique sizes are skipped.
        2. Cryptographic hashing only on collision candidates (files with identical sizes).
        """
        # Tier 1: Group files by exact size in bytes
        size_buckets: Dict[int, List[FileInfo]] = {}
        for f in files:
            # Skip empty 0-byte files from duplicate clumping or treat separately
            if f.size_bytes == 0:
                continue
            size_buckets.setdefault(f.size_bytes, []).append(f)

        candidates = [f for bucket in size_buckets.values() if len(bucket) > 1 for f in bucket]
        total_candidates = len(candidates)

        report = DuplicateReport()
        if total_candidates == 0:
            return report

        # Tier 2: Hash collision candidates
        hash_buckets: Dict[str, List[FileInfo]] = {}
        processed = 0

        for candidate in candidates:
            file_hash = self.compute_file_hash(candidate.path)
            if file_hash:
                report.hash_lookup[candidate.path] = file_hash
                hash_buckets.setdefault(file_hash, []).append(candidate)
            processed += 1
            if progress_callback:
                progress_callback(processed, total_candidates)

        # Assemble duplicate groups
        for file_hash, cluster in hash_buckets.items():
            if len(cluster) > 1:
                # Designate primary file: prioritize oldest creation date, then shortest path
                sorted_cluster = sorted(cluster, key=lambda f: (f.created_at, len(str(f.path))))
                primary = sorted_cluster[0]
                duplicates = sorted_cluster[1:]

                group = DuplicateGroup(
                    file_hash=file_hash,
                    size_bytes=primary.size_bytes,
                    primary_file=primary,
                    duplicate_files=duplicates,
                )
                report.groups.append(group)
                for dup in duplicates:
                    report.duplicate_paths[dup.path] = group

        report.groups.sort(key=lambda g: g.wasted_bytes, reverse=True)
        return report
