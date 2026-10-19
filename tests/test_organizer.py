"""Unit tests for the end-to-end organization engine, plan preview, execution, and rollback."""

from pathlib import Path
import pytest

from src.database import DatabaseManager
from src.rules import RuleEngine
from src.engine import (
    OrganizerEngine,
    ActionType,
    ConflictStrategy,
    DuplicateStrategy,
)
from src.classifier import DateGroupingMode


@pytest.fixture
def test_engine(tmp_path: Path) -> OrganizerEngine:
    db = DatabaseManager(db_path=tmp_path / "test_organizer.db")
    return OrganizerEngine(db_manager=db)


def test_organizer_plan_and_execution(test_engine: OrganizerEngine, tmp_path: Path) -> None:
    source_dir = tmp_path / "messy_source"
    source_dir.mkdir()

    # Create dummy files
    (source_dir / "Invoice_101.pdf").write_text("Invoice 101 content")
    (source_dir / "Screenshot_app.png").write_text("PNG image bytes")
    (source_dir / "script.py").write_text("print('test')")

    target_dir = tmp_path / "organized_output"

    # Build organization plan
    plan = test_engine.build_plan(
        source_dir=source_dir,
        target_dir=target_dir,
        date_mode=DateGroupingMode.NONE,
    )

    assert plan.total_files == 3
    assert plan.files_to_move == 3

    # Check planned destinations
    actions_by_name = {a.source_name: a for a in plan.actions}
    assert "Invoice_101.pdf" in actions_by_name
    assert "Finances" in str(actions_by_name["Invoice_101.pdf"].destination_path)
    assert "Screenshots" in str(actions_by_name["Screenshot_app.png"].destination_path)
    assert "Code & Scripts" in str(actions_by_name["script.py"].destination_path)

    # Execute plan
    result = test_engine.execute_plan(plan)
    assert result.success is True
    assert result.moved_count == 3
    assert result.failed_count == 0

    # Verify files moved to target destinations
    assert not (source_dir / "Invoice_101.pdf").exists()
    assert (target_dir / "Finances" / "Invoices" / "Invoice_101.pdf").exists()
    assert (target_dir / "Screenshots" / "Screenshot_app.png").exists()
    assert (target_dir / "Code & Scripts" / "script.py").exists()

    # Verify rollback/undo
    rollback_res = test_engine.rollback_batch(result.batch_id)
    assert rollback_res.restored_count == 3
    assert rollback_res.failed_count == 0

    # Verify files restored to original locations
    assert (source_dir / "Invoice_101.pdf").exists()
    assert (source_dir / "Screenshot_app.png").exists()
    assert (source_dir / "script.py").exists()


def test_organizer_collision_rename(test_engine: OrganizerEngine, tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    target_dir = tmp_path / "target"
    source_dir.mkdir()
    target_dir.mkdir()

    # Create source file
    (source_dir / "document.txt").write_text("Source document")

    # Create pre-existing file at target location
    dest_folder = target_dir / "Documents"
    dest_folder.mkdir(parents=True)
    (dest_folder / "document.txt").write_text("Pre-existing document")

    plan = test_engine.build_plan(
        source_dir=source_dir,
        target_dir=target_dir,
        conflict_strategy=ConflictStrategy.RENAME,
    )

    action = plan.actions[0]
    assert action.action_type == ActionType.RENAME_COLLISION
    assert action.destination_path.name == "document (1).txt"

    res = test_engine.execute_plan(plan)
    assert res.success is True
    assert (dest_folder / "document.txt").read_text() == "Pre-existing document"
    assert (dest_folder / "document (1).txt").read_text() == "Source document"
