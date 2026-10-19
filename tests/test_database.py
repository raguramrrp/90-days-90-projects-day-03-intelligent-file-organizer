"""Unit tests for SQLite database operations, batch logging, and rule persistence."""

from pathlib import Path
import pytest

from src.database import DatabaseManager
from src.rules import OrganizationRule, RuleCondition


@pytest.fixture
def test_db(tmp_path: Path) -> DatabaseManager:
    db_file = tmp_path / "test_audit.db"
    return DatabaseManager(db_path=db_file)


def test_database_initialization(test_db: DatabaseManager) -> None:
    # Ensure tables exist
    with test_db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = {row[0] for row in cursor.fetchall()}
        assert "batches" in tables
        assert "operations" in tables
        assert "rules" in tables


def test_database_batch_and_operations(test_db: DatabaseManager) -> None:
    batch_id = "test_batch_001"
    test_db.record_batch_start(batch_id, "/source/dir", "/target/dir", total_files=2)

    op1_id = test_db.log_operation(
        batch_id=batch_id,
        source="/source/dir/file1.txt",
        destination="/target/dir/Documents/file1.txt",
        status="MOVED",
        file_hash="mock_hash_1",
        file_size=1024,
        rule_matched="Default Category",
    )
    assert op1_id > 0

    op2_id = test_db.log_operation(
        batch_id=batch_id,
        source="/source/dir/file2.txt",
        destination="/target/dir/Documents/file2.txt",
        status="SKIPPED",
        file_hash="mock_hash_2",
        file_size=512,
        rule_matched="Skipped by user",
    )
    assert op2_id > 0

    test_db.update_batch_completion(batch_id, moved_files=1, skipped_files=1, failed_files=0)

    batches = test_db.get_batches()
    assert len(batches) == 1
    assert batches[0]["batch_id"] == batch_id
    assert batches[0]["moved_files"] == 1
    assert batches[0]["status"] == "COMPLETED"

    ops = test_db.get_batch_operations(batch_id)
    assert len(ops) == 2
    assert ops[0]["status"] == "MOVED"
    assert ops[1]["status"] == "SKIPPED"


def test_database_rules_crud(test_db: DatabaseManager) -> None:
    rule = OrganizationRule(
        name="Receipts Rule",
        target_folder="Receipts",
        priority=12,
        enabled=True,
        condition=RuleCondition(name_pattern="*receipt*"),
    )
    rule_id = test_db.save_rule(rule)
    assert rule_id > 0

    loaded = test_db.load_rules()
    assert len(loaded) == 1
    assert loaded[0].name == "Receipts Rule"
    assert loaded[0].priority == 12

    # Update rule
    loaded[0].name = "Updated Receipts"
    loaded[0].enabled = False
    test_db.save_rule(loaded[0])

    updated_rules = test_db.load_rules()
    assert updated_rules[0].name == "Updated Receipts"
    assert updated_rules[0].enabled is False

    # Delete rule
    deleted = test_db.delete_rule(rule_id)
    assert deleted is True
    assert len(test_db.load_rules()) == 0


def test_database_export(test_db: DatabaseManager, tmp_path: Path) -> None:
    batch_id = "export_batch"
    test_db.record_batch_start(batch_id, "/src", "/dst", 1)
    test_db.log_operation(
        batch_id=batch_id,
        source="/src/file.pdf",
        destination="/dst/file.pdf",
        status="MOVED",
        file_hash="abc123hash",
        file_size=4096,
        rule_matched="Rule A",
    )

    csv_path = tmp_path / "export.csv"
    count_csv = test_db.export_audit_csv(csv_path)
    assert count_csv == 1
    assert csv_path.exists()
    assert "abc123hash" in csv_path.read_text(encoding="utf-8")

    json_path = tmp_path / "export.json"
    count_json = test_db.export_audit_json(json_path)
    assert count_json == 1
    assert json_path.exists()
    assert "export_batch" in json_path.read_text(encoding="utf-8")
