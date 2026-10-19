"""Database module for SQLite transaction audit logs, batch tracking, and rules."""

from __future__ import annotations

import csv
import json
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from src.rules import OrganizationRule, RuleCondition

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages SQLite database connections, schema migrations, and audit logging."""

    DEFAULT_DB_NAME = "file_organizer.db"

    def __init__(self, db_path: Optional[Path | str] = None) -> None:
        if db_path is None:
            self.db_path = Path.cwd() / self.DEFAULT_DB_NAME
        else:
            self.db_path = Path(db_path)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        """Create and configure a new SQLite connection with foreign keys and WAL mode."""
        conn = sqlite3.connect(str(self.db_path), timeout=20.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        return conn

    def init_db(self) -> None:
        """Create database tables and performance indexes if they do not exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 1. Batches table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS batches (
                    batch_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    source_dir TEXT NOT NULL,
                    target_dir TEXT NOT NULL,
                    total_files INTEGER NOT NULL DEFAULT 0,
                    moved_files INTEGER NOT NULL DEFAULT 0,
                    skipped_files INTEGER NOT NULL DEFAULT 0,
                    failed_files INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL DEFAULT 'IN_PROGRESS'
                );
            """)

            # 2. Operations table matching specification:
            # operations(id, source, destination, timestamp, status)
            # plus batch_id, file_hash, file_size, rule_matched, error_message
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS operations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    batch_id TEXT NOT NULL,
                    source TEXT NOT NULL,
                    destination TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    status TEXT NOT NULL,
                    file_hash TEXT,
                    file_size INTEGER DEFAULT 0,
                    rule_matched TEXT,
                    error_message TEXT,
                    FOREIGN KEY (batch_id) REFERENCES batches(batch_id) ON DELETE CASCADE
                );
            """)

            # 3. Rules table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    priority INTEGER NOT NULL DEFAULT 100,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    target_folder TEXT NOT NULL,
                    condition_json TEXT NOT NULL
                );
            """)

            # Indexes for quick query filtering
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ops_batch ON operations(batch_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ops_status ON operations(status);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_batches_date ON batches(created_at DESC);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rules_priority ON rules(priority ASC);")

            conn.commit()

    # =========================================================================
    # Batch & Operations Audit Logging
    # =========================================================================

    def record_batch_start(
        self,
        batch_id: str,
        source_dir: str,
        target_dir: str,
        total_files: int,
    ) -> None:
        """Log the initiation of an organization batch."""
        timestamp = datetime.now().isoformat()
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO batches (batch_id, created_at, source_dir, target_dir, total_files, status)
                VALUES (?, ?, ?, ?, ?, 'IN_PROGRESS')
                """,
                (batch_id, timestamp, source_dir, target_dir, total_files)
            )
            conn.commit()

    def update_batch_completion(
        self,
        batch_id: str,
        moved_files: int,
        skipped_files: int,
        failed_files: int,
        status: str = "COMPLETED",
    ) -> None:
        """Update batch outcome statistics upon execution completion."""
        with self.get_connection() as conn:
            conn.execute(
                """
                UPDATE batches
                SET moved_files = ?, skipped_files = ?, failed_files = ?, status = ?
                WHERE batch_id = ?
                """,
                (moved_files, skipped_files, failed_files, status, batch_id)
            )
            conn.commit()

    def log_operation(
        self,
        batch_id: str,
        source: str,
        destination: str,
        status: str,
        file_hash: Optional[str] = None,
        file_size: int = 0,
        rule_matched: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> int:
        """Insert a single filesystem operation record into the audit table."""
        timestamp = datetime.now().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO operations (
                    batch_id, source, destination, timestamp, status,
                    file_hash, file_size, rule_matched, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    batch_id, source, destination, timestamp, status,
                    file_hash, file_size, rule_matched, error_message
                )
            )
            conn.commit()
            return cursor.lastrowid or 0

    def get_batches(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve recent organization batches ordered by timestamp descending."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT batch_id, created_at, source_dir, target_dir,
                       total_files, moved_files, skipped_files, failed_files, status
                FROM batches
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,)
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_batch_operations(self, batch_id: str) -> List[Dict[str, Any]]:
        """Retrieve all individual file movements logged for a specific batch."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, batch_id, source, destination, timestamp, status,
                       file_hash, file_size, rule_matched, error_message
                FROM operations
                WHERE batch_id = ?
                ORDER BY id ASC
                """,
                (batch_id,)
            )
            return [dict(row) for row in cursor.fetchall()]

    def mark_batch_rolled_back(self, batch_id: str) -> None:
        """Flag batch as rolled back and update associated operations."""
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE batches SET status = 'ROLLED_BACK' WHERE batch_id = ?",
                (batch_id,)
            )
            conn.execute(
                "UPDATE operations SET status = 'ROLLED_BACK' WHERE batch_id = ? AND status = 'MOVED'",
                (batch_id,)
            )
            conn.commit()

    def get_stats(self) -> Dict[str, Any]:
        """Compute aggregated operational metrics."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM batches;")
            total_batches = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*), COALESCE(SUM(file_size), 0) FROM operations WHERE status = 'MOVED';")
            moved_row = cursor.fetchone()
            total_moved = moved_row[0]
            total_bytes = moved_row[1]

            cursor.execute("SELECT COUNT(*) FROM operations WHERE status = 'ROLLED_BACK';")
            total_rolled_back = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM rules WHERE enabled = 1;")
            active_rules = cursor.fetchone()[0]

            return {
                "total_batches": total_batches,
                "total_files_moved": total_moved,
                "total_bytes_moved": total_bytes,
                "total_rolled_back": total_rolled_back,
                "active_rules_count": active_rules,
            }

    # =========================================================================
    # Rule Persistence
    # =========================================================================

    def load_rules(self) -> List[OrganizationRule]:
        """Fetch all user-defined and stored rules from database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, name, priority, enabled, target_folder, condition_json FROM rules ORDER BY priority ASC, name ASC"
            )
            rules: List[OrganizationRule] = []
            for row in cursor.fetchall():
                try:
                    cond_dict = json.loads(row["condition_json"])
                    rule = OrganizationRule(
                        id=row["id"],
                        name=row["name"],
                        priority=row["priority"],
                        enabled=bool(row["enabled"]),
                        target_folder=row["target_folder"],
                        condition=RuleCondition.from_dict(cond_dict),
                    )
                    rules.append(rule)
                except Exception as exc:
                    logger.warning("Error parsing rule %s: %s", row["id"], exc)
            return rules

    def save_rule(self, rule: OrganizationRule) -> int:
        """Insert or update an organization rule."""
        cond_json = json.dumps(rule.condition.to_dict())
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if rule.id is not None:
                cursor.execute(
                    """
                    UPDATE rules
                    SET name = ?, priority = ?, enabled = ?, target_folder = ?, condition_json = ?
                    WHERE id = ?
                    """,
                    (rule.name, rule.priority, 1 if rule.enabled else 0, rule.target_folder, cond_json, rule.id)
                )
                conn.commit()
                return rule.id
            else:
                cursor.execute(
                    """
                    INSERT INTO rules (name, priority, enabled, target_folder, condition_json)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (rule.name, rule.priority, 1 if rule.enabled else 0, rule.target_folder, cond_json)
                )
                conn.commit()
                rule.id = cursor.lastrowid
                return rule.id or 0

    def delete_rule(self, rule_id: int) -> bool:
        """Remove a rule by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM rules WHERE id = ?", (rule_id,))
            conn.commit()
            return cursor.rowcount > 0

    def initialize_default_rules_if_empty(self, default_rules: List[OrganizationRule]) -> None:
        """Populate database with starter rules if no rules currently exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM rules;")
            count = cursor.fetchone()[0]
            if count == 0:
                for rule in default_rules:
                    cond_json = json.dumps(rule.condition.to_dict())
                    cursor.execute(
                        """
                        INSERT INTO rules (name, priority, enabled, target_folder, condition_json)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (rule.name, rule.priority, 1 if rule.enabled else 0, rule.target_folder, cond_json)
                    )
                conn.commit()

    # =========================================================================
    # Export Helpers
    # =========================================================================

    def export_audit_csv(self, export_path: Path | str) -> int:
        """Export all operations history into a standard CSV file."""
        target = Path(export_path)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, batch_id, source, destination, timestamp, status,
                       file_hash, file_size, rule_matched, error_message
                FROM operations
                ORDER BY id ASC
                """
            )
            rows = cursor.fetchall()
            if not rows:
                return 0

            with open(target, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(rows[0].keys())
                for row in rows:
                    writer.writerow(tuple(row))
            return len(rows)

    def export_audit_json(self, export_path: Path | str) -> int:
        """Export all operations history into structured JSON format."""
        target = Path(export_path)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, batch_id, source, destination, timestamp, status,
                       file_hash, file_size, rule_matched, error_message
                FROM operations
                ORDER BY id ASC
                """
            )
            records = [dict(row) for row in cursor.fetchall()]
            with open(target, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2)
            return len(records)
