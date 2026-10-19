"""Unified entrypoint for the Intelligent File Organizer application (GUI and CLI modes)."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is available on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import argparse
import logging

from src.scanner import FileScanner, format_bytes
from src.classifier import DateGroupingMode, HierarchyStyle
from src.rules import OrganizationRule
from src.duplicates import DuplicateStrategy
from src.database import DatabaseManager
from src.engine import (
    OrganizerEngine,
    ConflictStrategy,
)


def setup_logging(verbose: bool = False) -> None:
    """Configure console logging level and format."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def run_cli(args: argparse.Namespace) -> int:
    """Execute command-line automation workflow without displaying GUI."""
    engine = OrganizerEngine()

    # 1. Statistics Command
    if args.stats:
        stats = engine.db.get_stats()
        print("\n" + "=" * 55)
        print("   CONTEXT-AWARE FILE ORGANIZER - SYSTEM METRICS")
        print("=" * 55)
        print(f"Total Batches Recorded   : {stats['total_batches']}")
        print(f"Total Files Organized    : {stats['total_files_moved']}")
        print(f"Total Data Transferred   : {format_bytes(stats['total_bytes_moved'])}")
        print(f"Total Operations Rolled Back: {stats['total_rolled_back']}")
        print(f"Active Organization Rules: {stats['active_rules_count']}")
        print("=" * 55 + "\n")
        return 0

    # 2. List Rules Command
    if args.list_rules:
        rules = engine.db.load_rules()
        print("\n" + "=" * 65)
        print("   CONFIGURED ORGANIZATION RULES (PRIORITY ORDER)")
        print("=" * 65)
        for r in rules:
            status = "ENABLED " if r.enabled else "DISABLED"
            print(f"[{status}] (Priority {r.priority:3d}) {r.name:25s} -> {r.target_folder}")
        print("=" * 65 + "\n")
        return 0

    # 3. Rollback / Undo Batch Command
    if args.undo:
        batch_id = args.undo.strip()
        print(f"\n[INITIATING ROLLBACK] Restoring files for batch: {batch_id}...")
        res = engine.rollback_batch(batch_id)
        print(f"Restored Files: {res.restored_count}")
        print(f"Failed Restorations: {res.failed_count}")
        if res.errors:
            for fname, err in res.errors:
                print(f"  - Warning on {fname}: {err}")
        return 0 if res.failed_count == 0 else 1

    # 4. Export Audit History
    if args.export_csv:
        count = engine.db.export_audit_csv(args.export_csv)
        print(f"Exported {count} operations records to {args.export_csv}")
        return 0

    # 5. Scan / Preview / Organize
    target_dir = args.scan or args.organize or args.dry_run
    if not target_dir:
        print("[ERROR] Please specify a directory to scan or organize via --scan, --dry-run, or --organize.")
        return 1

    source_path = Path(target_dir).resolve()
    if not source_path.exists() or not source_path.is_dir():
        print(f"[ERROR] Target directory does not exist or is not a folder: {source_path}")
        return 1

    output_dir = Path(args.dest).resolve() if args.dest else source_path
    date_mode = DateGroupingMode(args.date_grouping)
    hierarchy = HierarchyStyle(args.hierarchy)
    conflict = ConflictStrategy(args.conflict)
    dup_strat = DuplicateStrategy(args.duplicates)

    print("\n" + "=" * 65)
    print("   CONTEXT-AWARE FILE ORGANIZER - SIMULATION & SCAN")
    print("=" * 65)
    print(f"Source Folder : {source_path}")
    print(f"Target Folder : {output_dir}")
    print(f"Date Grouping : {date_mode.value}")
    print(f"Hierarchy     : {hierarchy.value}")
    print(f"Conflict Mode : {conflict.value}")
    print(f"Duplicate Mode: {dup_strat.value}")
    print("-" * 65)

    plan = engine.build_plan(
        source_dir=source_path,
        target_dir=output_dir,
        recursive=args.recursive,
        include_hidden=args.include_hidden,
        date_mode=date_mode,
        hierarchy=hierarchy,
        conflict_strategy=conflict,
        duplicate_strategy=dup_strat,
    )

    print(f"Discovered Files : {plan.total_files}")
    print(f"Scheduled Moves  : {plan.files_to_move}")
    print(f"Duplicates Found : {plan.duplicate_report.total_duplicates} ({plan.duplicate_report.readable_wasted_space} wasted)")
    print("-" * 65)

    for action in plan.actions[:30]:
        flag = f"[{action.action_type.value}]"
        print(f"{flag:18s} {action.source_name:24s} -> {str(action.relative_dest):30s} ({action.size_readable})")

    if len(plan.actions) > 30:
        print(f"... and {len(plan.actions) - 30} more items.")

    # If --dry-run or --scan, stop here
    if args.dry_run or args.scan:
        print("-" * 65)
        print("[DRY RUN COMPLETE] No files were modified on disk.")
        print("=" * 65 + "\n")
        return 0

    # Execute moves if --organize was requested
    if args.organize:
        print("\nExecuting filesystem changes...")
        res = engine.execute_plan(plan)
        print("-" * 65)
        print(f"[EXECUTION COMPLETE] Batch ID: {res.batch_id}")
        print(f"Moved Files : {res.moved_count}")
        print(f"Skipped     : {res.skipped_count}")
        print(f"Failed      : {res.failed_count}")
        print(f"Data Moved  : {format_bytes(res.total_bytes_moved)}")
        print("=" * 65 + "\n")
        return 0 if res.success else 1

    return 0


def main() -> None:
    """Main CLI / GUI dispatch entrypoint."""
    parser = argparse.ArgumentParser(
        description="Context-Aware Desktop File Organization Automation Engine",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument("--gui", action="store_true", help="Launch interactive graphical user interface (default)")
    parser.add_argument("--scan", type=str, metavar="DIR", help="Scan and inspect directory contents without moving")
    parser.add_argument("--dry-run", type=str, metavar="DIR", help="Simulate organization plan without altering files")
    parser.add_argument("--organize", type=str, metavar="DIR", help="Execute organization moves on target directory")
    parser.add_argument("--dest", type=str, metavar="DIR", help="Destination folder (defaults to same as source)")

    parser.add_argument(
        "--date-grouping",
        choices=[m.value for m in DateGroupingMode],
        default=DateGroupingMode.NONE.value,
        help="Date sub-folder grouping strategy"
    )
    parser.add_argument(
        "--hierarchy",
        choices=[h.value for h in HierarchyStyle],
        default=HierarchyStyle.CATEGORY_FIRST.value,
        help="Folder hierarchy layout"
    )
    parser.add_argument(
        "--conflict",
        choices=[c.value for c in ConflictStrategy],
        default=ConflictStrategy.RENAME.value,
        help="Target collision resolution strategy"
    )
    parser.add_argument(
        "--duplicates",
        choices=[d.value for d in DuplicateStrategy],
        default=DuplicateStrategy.REPORT_ONLY.value,
        help="Duplicate handling strategy"
    )
    parser.add_argument("--recursive", action="store_true", help="Traverse nested subdirectories")
    parser.add_argument("--include-hidden", action="store_true", help="Include hidden system files")
    parser.add_argument("--stats", action="store_true", help="Print overall historical organization statistics")
    parser.add_argument("--list-rules", action="store_true", help="Display all active organization rules")
    parser.add_argument("--undo", type=str, metavar="BATCH_ID", help="Roll back and restore all files from a batch")
    parser.add_argument("--export-csv", type=str, metavar="PATH", help="Export audit operations history to CSV")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose debug logging")

    args = parser.parse_args()
    setup_logging(args.verbose)

    # Determine whether to run CLI or GUI
    cli_flags = [
        args.scan, args.dry_run, args.organize,
        args.stats, args.list_rules, args.undo, args.export_csv
    ]

    if any(cli_flags) and not args.gui:
        sys.exit(run_cli(args))
    else:
        # Launch Tkinter GUI
        from src.ui.app import FileOrganizerApp
        app = FileOrganizerApp()
        app.mainloop()


if __name__ == "__main__":
    main()
