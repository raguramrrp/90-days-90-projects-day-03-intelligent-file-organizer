"""Core workflow engine coordinating scanning, classification, preview, execution, and rollback."""

from __future__ import annotations

import os
import shutil
import uuid
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set, Tuple

from src.scanner import FileInfo, FileScanner, format_bytes
from src.classifier import FileClassifier, DateGroupingMode, HierarchyStyle
from src.rules import RuleEngine, OrganizationRule
from src.duplicates import DuplicateDetector, DuplicateReport, DuplicateStrategy
from src.database import DatabaseManager

logger = logging.getLogger(__name__)


class ConflictStrategy(str, Enum):
    """Behavior when a target filename already exists in the destination folder."""
    RENAME = "rename"          # Append index: filename (1).ext
    SKIP = "skip"              # Do not move the source file
    OVERWRITE = "overwrite"    # Replace existing file at destination


class ActionType(str, Enum):
    """Categorized action scheduled for a single file entry."""
    MOVE = "MOVE"
    SKIP = "SKIP"
    RENAME_COLLISION = "RENAME_COLLISION"
    QUARANTINE_DUPLICATE = "QUARANTINE_DUPLICATE"


@dataclass
class PlannedAction:
    """Action item generated during preview simulation."""
    source_file: FileInfo
    destination_path: Path
    relative_dest: Path
    action_type: ActionType
    category: str
    matched_rule: Optional[str] = None
    is_duplicate: bool = False
    duplicate_of: Optional[Path] = None
    file_hash: Optional[str] = None
    original_target_exists: bool = False
    included: bool = True  # Can be toggled in GUI preview

    @property
    def source_name(self) -> str:
        return self.source_file.name

    @property
    def size_readable(self) -> str:
        return self.source_file.readable_size


@dataclass
class OrganizationPlan:
    """Previewable simulation of all file movements before applying changes."""
    source_dir: Path
    target_dir: Path
    actions: List[PlannedAction] = field(default_factory=list)
    duplicate_report: DuplicateReport = field(default_factory=DuplicateReport)
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def total_files(self) -> int:
        return len(self.actions)

    @property
    def files_to_move(self) -> int:
        return sum(1 for a in self.actions if a.included and a.action_type != ActionType.SKIP)

    @property
    def total_bytes_to_move(self) -> int:
        return sum(a.source_file.size_bytes for a in self.actions if a.included and a.action_type != ActionType.SKIP)

    @property
    def category_distribution(self) -> Dict[str, int]:
        dist: Dict[str, int] = {}
        for a in self.actions:
            dist[a.category] = dist.get(a.category, 0) + 1
        return dist


@dataclass
class ExecutionResult:
    """Summary metrics of executed organization batch."""
    batch_id: str
    total_planned: int
    moved_count: int
    skipped_count: int
    failed_count: int
    total_bytes_moved: int
    errors: List[Tuple[str, str]] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return self.failed_count == 0


@dataclass
class RollbackResult:
    """Outcome of batch undo / rollback procedure."""
    batch_id: str
    restored_count: int
    failed_count: int
    errors: List[Tuple[str, str]] = field(default_factory=list)


class OrganizerEngine:
    """High-level facade driving the complete file organization workflow."""

    def __init__(
        self,
        db_manager: Optional[DatabaseManager] = None,
        rule_engine: Optional[RuleEngine] = None,
        classifier: Optional[FileClassifier] = None,
        detector: Optional[DuplicateDetector] = None,
    ) -> None:
        self.db = db_manager or DatabaseManager()
        self.classifier = classifier or FileClassifier()
        self.detector = detector or DuplicateDetector()
        
        # Initialize rules
        if rule_engine:
            self.rules = rule_engine
        else:
            loaded_rules = self.db.load_rules()
            if not loaded_rules:
                self.rules = RuleEngine()
                self.db.initialize_default_rules_if_empty(self.rules.rules)
            else:
                self.rules = RuleEngine(loaded_rules)

    def _resolve_collision_name(self, dest_path: Path) -> Path:
        """Find non-colliding filename by appending incremental counter: (1), (2), etc."""
        parent = dest_path.parent
        stem = dest_path.stem
        ext = dest_path.suffix
        counter = 1
        candidate = dest_path
        while candidate.exists():
            candidate = parent / f"{stem} ({counter}){ext}"
            counter += 1
        return candidate

    def build_plan(
        self,
        source_dir: Path | str,
        target_dir: Optional[Path | str] = None,
        recursive: bool = False,
        include_hidden: bool = False,
        date_mode: DateGroupingMode = DateGroupingMode.NONE,
        hierarchy: HierarchyStyle = HierarchyStyle.CATEGORY_FIRST,
        conflict_strategy: ConflictStrategy = ConflictStrategy.RENAME,
        duplicate_strategy: DuplicateStrategy = DuplicateStrategy.REPORT_ONLY,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> OrganizationPlan:
        """Scan source directory, apply rules and classification, and assemble preview plan."""
        source_path = Path(source_dir).resolve()
        target_path = Path(target_dir).resolve() if target_dir else source_path

        if not source_path.exists() or not source_path.is_dir():
            raise ValueError(f"Source folder does not exist: {source_path}")

        # Safety: avoid re-scanning organized subfolders whether target is inside source or not
        excluded_dirs: Set[str] = {
            cat.lower() for cat in self.classifier.DEFAULT_EXT_MAP.keys()
        } | {"_duplicates", "screenshots", "finances", "career", "large_files", "software_installers"}

        # If target directory is inside or equal to source directory, exclude it so output files aren't scanned
        try:
            rel_to_source = target_path.relative_to(source_path)
            if len(rel_to_source.parts) > 0:
                excluded_dirs.add(rel_to_source.parts[0].lower())
        except ValueError:
            pass

        scanner = FileScanner(
            include_hidden=include_hidden,
            exclude_dirs=excluded_dirs,
        )

        if progress_callback:
            progress_callback("Scanning directory for eligible files...", 5, 100)

        def scan_prog(count: int, fname: str) -> None:
            if progress_callback:
                progress_callback(f"Scanning directory: {count} files discovered...", 15, 100)

        files = scanner.scan_directory(source_path, recursive=recursive, progress_callback=scan_prog)

        if progress_callback:
            progress_callback(f"Scanned {len(files)} files. Analyzing duplicate candidates...", 35, 100)

        def dup_prog(cur: int, tot: int) -> None:
            if progress_callback:
                pct = 35 + int((cur / tot) * 35) if tot > 0 else 70
                progress_callback(f"Analyzing duplicate signatures ({cur}/{tot})...", pct, 100)

        # Run duplicate detection with progress callback
        dup_report = self.detector.detect_duplicates(files, progress_callback=dup_prog)

        if progress_callback:
            progress_callback(f"Evaluating classification rules for {len(files)} files...", 72, 100)

        actions: List[PlannedAction] = []
        claimed_destinations: Set[Path] = set()
        total_files = len(files)

        for idx, file_info in enumerate(files, start=1):
            if progress_callback and (idx % 100 == 0 or idx == total_files):
                pct = 72 + int((idx / total_files) * 26) if total_files > 0 else 98
                progress_callback(f"Compiling organization plan ({idx}/{total_files})...", pct, 100)
            is_duplicate = file_info.path in dup_report.duplicate_paths
            duplicate_group = dup_report.duplicate_paths.get(file_info.path)
            primary_path = duplicate_group.primary_file.path if duplicate_group else None
            file_hash = dup_report.hash_lookup.get(file_info.path)

            # Check duplicate strategy override
            if is_duplicate and duplicate_strategy == DuplicateStrategy.SKIP:
                action = PlannedAction(
                    source_file=file_info,
                    destination_path=file_info.path,
                    relative_dest=Path(file_info.name),
                    action_type=ActionType.SKIP,
                    category="Duplicates",
                    matched_rule="Duplicate: Skipped",
                    is_duplicate=True,
                    duplicate_of=primary_path,
                    file_hash=file_hash,
                    included=False,
                )
                actions.append(action)
                continue

            # Determine destination folder
            dest_folder: Path
            matched_rule_name: Optional[str] = None
            category_name: str

            if is_duplicate and duplicate_strategy == DuplicateStrategy.QUARANTINE:
                dest_folder = Path("_Duplicates")
                category_name = "Duplicates"
                matched_rule_name = "Duplicate: Quarantine"
            else:
                rule_match = self.rules.evaluate(file_info)
                if rule_match:
                    rule, folder = rule_match
                    dest_folder = folder
                    matched_rule_name = f"Rule: {rule.name}"
                    category_name = rule.name
                else:
                    dest_folder = self.classifier.compute_destination_folder(
                        file_info,
                        date_mode=date_mode,
                        hierarchy=hierarchy,
                    )
                    category_name = self.classifier.get_category(file_info)

            # Proposed full target path
            proposed_dest = target_path / dest_folder / file_info.name
            relative_dest = dest_folder / file_info.name

            # Check if source and proposed destination are identical
            if file_info.path.resolve() == proposed_dest.resolve():
                action = PlannedAction(
                    source_file=file_info,
                    destination_path=proposed_dest,
                    relative_dest=relative_dest,
                    action_type=ActionType.SKIP,
                    category=category_name,
                    matched_rule="Already in target location",
                    is_duplicate=is_duplicate,
                    duplicate_of=primary_path,
                    file_hash=file_hash,
                    included=False,
                )
                actions.append(action)
                continue

            # Conflict handling
            original_exists = proposed_dest.exists() or proposed_dest in claimed_destinations
            final_dest = proposed_dest
            action_type = ActionType.MOVE

            if original_exists:
                if conflict_strategy == ConflictStrategy.SKIP:
                    action_type = ActionType.SKIP
                elif conflict_strategy == ConflictStrategy.OVERWRITE:
                    action_type = ActionType.MOVE
                elif conflict_strategy == ConflictStrategy.RENAME:
                    final_dest = self._resolve_collision_name(proposed_dest)
                    # Also guard against multiple files colliding with the same new name in the same batch
                    while final_dest in claimed_destinations:
                        final_dest = self._resolve_collision_name(final_dest)
                    action_type = ActionType.RENAME_COLLISION

            claimed_destinations.add(final_dest)

            action = PlannedAction(
                source_file=file_info,
                destination_path=final_dest,
                relative_dest=relative_dest,
                action_type=action_type,
                category=category_name,
                matched_rule=matched_rule_name,
                is_duplicate=is_duplicate,
                duplicate_of=primary_path,
                file_hash=file_hash,
                original_target_exists=original_exists,
                included=action_type != ActionType.SKIP,
            )
            actions.append(action)

        if progress_callback:
            progress_callback("Plan generated successfully.", 100, 100)

        return OrganizationPlan(
            source_dir=source_path,
            target_dir=target_path,
            actions=actions,
            duplicate_report=dup_report,
        )

    def execute_plan(
        self,
        plan: OrganizationPlan,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> ExecutionResult:
        """Execute approved plan movements with atomic filesystem operations and database audit."""
        batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        
        eligible_actions = [a for a in plan.actions if a.included and a.action_type != ActionType.SKIP]
        total_actions = len(eligible_actions)

        self.db.record_batch_start(
            batch_id=batch_id,
            source_dir=str(plan.source_dir),
            target_dir=str(plan.target_dir),
            total_files=total_actions,
        )

        moved_count = 0
        skipped_count = 0
        failed_count = 0
        total_bytes_moved = 0
        errors: List[Tuple[str, str]] = []

        # Count actions that were deliberately excluded as skipped
        for a in plan.actions:
            if not a.included or a.action_type == ActionType.SKIP:
                skipped_count += 1
                self.db.log_operation(
                    batch_id=batch_id,
                    source=str(a.source_file.path),
                    destination=str(a.destination_path),
                    status="SKIPPED",
                    file_hash=a.file_hash,
                    file_size=a.source_file.size_bytes,
                    rule_matched=a.matched_rule,
                )

        # Execute eligible moves
        for idx, action in enumerate(eligible_actions, start=1):
            src = action.source_file.path
            dst = action.destination_path

            if progress_callback:
                progress_callback(idx, total_actions, action.source_name)

            try:
                # Ensure destination directory exists
                dst.parent.mkdir(parents=True, exist_ok=True)

                # Execute filesystem move
                shutil.move(str(src), str(dst))

                # Log operation in SQLite
                self.db.log_operation(
                    batch_id=batch_id,
                    source=str(src),
                    destination=str(dst),
                    status="MOVED",
                    file_hash=action.file_hash,
                    file_size=action.source_file.size_bytes,
                    rule_matched=action.matched_rule,
                )

                moved_count += 1
                total_bytes_moved += action.source_file.size_bytes

            except Exception as exc:
                logger.error("Failed to move %s to %s: %s", src, dst, exc)
                failed_count += 1
                err_msg = str(exc)
                errors.append((src.name, err_msg))

                self.db.log_operation(
                    batch_id=batch_id,
                    source=str(src),
                    destination=str(dst),
                    status="FAILED",
                    file_hash=action.file_hash,
                    file_size=action.source_file.size_bytes,
                    rule_matched=action.matched_rule,
                    error_message=err_msg,
                )

        batch_status = "COMPLETED" if failed_count == 0 else "PARTIAL_FAILURE"
        self.db.update_batch_completion(
            batch_id=batch_id,
            moved_files=moved_count,
            skipped_files=skipped_count,
            failed_files=failed_count,
            status=batch_status,
        )

        return ExecutionResult(
            batch_id=batch_id,
            total_planned=total_actions,
            moved_count=moved_count,
            skipped_count=skipped_count,
            failed_count=failed_count,
            total_bytes_moved=total_bytes_moved,
            errors=errors,
        )

    def rollback_batch(
        self,
        batch_id: str,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> RollbackResult:
        """Safely restore moved files to their exact original locations using the audit log."""
        operations = self.db.get_batch_operations(batch_id)
        moved_ops = [op for op in operations if op["status"] == "MOVED"]

        restored_count = 0
        failed_count = 0
        errors: List[Tuple[str, str]] = []
        total = len(moved_ops)

        for idx, op in enumerate(reversed(moved_ops), start=1):
            curr_path = Path(op["destination"])
            orig_path = Path(op["source"])

            if progress_callback:
                progress_callback(idx, total, curr_path.name)

            try:
                if not curr_path.exists():
                    raise FileNotFoundError(f"Organized file no longer found at: {curr_path}")

                orig_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(curr_path), str(orig_path))
                restored_count += 1

            except Exception as exc:
                logger.error("Rollback failed for %s: %s", curr_path, exc)
                failed_count += 1
                errors.append((curr_path.name, str(exc)))

        if restored_count > 0 or failed_count == 0:
            self.db.mark_batch_rolled_back(batch_id)

        return RollbackResult(
            batch_id=batch_id,
            restored_count=restored_count,
            failed_count=failed_count,
            errors=errors,
        )
