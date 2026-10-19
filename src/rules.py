"""Rule engine module for evaluating customizable file organization criteria."""

from __future__ import annotations

import re
import fnmatch
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple, Any, Dict
from src.scanner import FileInfo


@dataclass
class RuleCondition:
    """Predicates evaluated against file properties to determine rule match."""
    name_pattern: Optional[str] = None          # e.g., "*invoice*", "Screenshot*", "regex:^IMG_\\d+"
    extensions: Optional[List[str]] = None       # e.g., [".pdf", ".xlsx"]
    min_size_bytes: Optional[int] = None         # bytes inclusive
    max_size_bytes: Optional[int] = None         # bytes inclusive
    older_than_days: Optional[int] = None        # days since modification
    newer_than_days: Optional[int] = None        # days since modification

    def to_dict(self) -> Dict[str, Any]:
        """Convert condition to serializable dictionary."""
        return {
            "name_pattern": self.name_pattern,
            "extensions": [ext.lower() for ext in self.extensions] if self.extensions else None,
            "min_size_bytes": self.min_size_bytes,
            "max_size_bytes": self.max_size_bytes,
            "older_than_days": self.older_than_days,
            "newer_than_days": self.newer_than_days,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RuleCondition:
        """Instantiate RuleCondition from dictionary payload."""
        return cls(
            name_pattern=data.get("name_pattern"),
            extensions=data.get("extensions"),
            min_size_bytes=data.get("min_size_bytes"),
            max_size_bytes=data.get("max_size_bytes"),
            older_than_days=data.get("older_than_days"),
            newer_than_days=data.get("newer_than_days"),
        )


@dataclass
class OrganizationRule:
    """User-defined or built-in categorization rule with priority ordering."""
    name: str
    target_folder: str
    condition: RuleCondition
    priority: int = 100
    enabled: bool = True
    id: Optional[int] = None

    def matches(self, file_info: FileInfo) -> bool:
        """Check whether the given file fulfills all defined criteria of this rule."""
        if not self.enabled:
            return False

        cond = self.condition

        # 1. Name pattern matching
        if cond.name_pattern:
            pattern = cond.name_pattern.strip()
            if pattern.startswith("regex:"):
                raw_regex = pattern[6:].strip()
                try:
                    if not re.search(raw_regex, file_info.name, re.IGNORECASE):
                        return False
                except re.error:
                    return False
            else:
                if not fnmatch.fnmatch(file_info.name.lower(), pattern.lower()):
                    return False

        # 2. Extension matching
        if cond.extensions:
            normalized_extensions = {ext.lower() if ext.startswith(".") else f".{ext.lower()}" for ext in cond.extensions}
            if file_info.extension.lower() not in normalized_extensions:
                return False

        # 3. Minimum size threshold
        if cond.min_size_bytes is not None:
            if file_info.size_bytes < cond.min_size_bytes:
                return False

        # 4. Maximum size threshold
        if cond.max_size_bytes is not None:
            if file_info.size_bytes > cond.max_size_bytes:
                return False

        # 5. Temporal age constraints (based on modified_at)
        now = datetime.now()
        age_days = (now - file_info.modified_at).total_seconds() / 86400.0

        if cond.older_than_days is not None:
            if age_days < cond.older_than_days:
                return False

        if cond.newer_than_days is not None:
            if age_days > cond.newer_than_days:
                return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert rule to serializable dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "target_folder": self.target_folder,
            "priority": self.priority,
            "enabled": self.enabled,
            "condition": self.condition.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> OrganizationRule:
        """Instantiate OrganizationRule from dictionary."""
        return cls(
            id=data.get("id"),
            name=data["name"],
            target_folder=data["target_folder"],
            priority=data.get("priority", 100),
            enabled=data.get("enabled", True),
            condition=RuleCondition.from_dict(data.get("condition", {})),
        )


class RuleEngine:
    """Manages rule registration, priority sorting, and file evaluation."""

    def __init__(self, rules: Optional[List[OrganizationRule]] = None) -> None:
        self.rules: List[OrganizationRule] = []
        if rules:
            for rule in rules:
                self.add_rule(rule)
        else:
            self.load_default_rules()

    def add_rule(self, rule: OrganizationRule) -> None:
        """Register a new rule and keep rules sorted by ascending priority."""
        self.rules.append(rule)
        self.sort_rules()

    def sort_rules(self) -> None:
        """Sort rules by priority (lower number = higher precedence)."""
        self.rules.sort(key=lambda r: (r.priority, r.name))

    def evaluate(self, file_info: FileInfo) -> Optional[Tuple[OrganizationRule, Path]]:
        """Evaluate file against all enabled rules in priority order.
        
        Returns:
            Tuple of (matched_rule, destination_folder_path) or None if no match.
        """
        for rule in self.rules:
            if rule.matches(file_info):
                return rule, Path(rule.target_folder)
        return None

    def load_default_rules(self) -> None:
        """Initialize sensible pre-configured starter rules."""
        self.rules = [
            OrganizationRule(
                id=1,
                name="Screenshots",
                priority=10,
                enabled=True,
                target_folder="Screenshots",
                condition=RuleCondition(
                    name_pattern="*screenshot*",
                    extensions=[".png", ".jpg", ".jpeg", ".webp"]
                ),
            ),
            OrganizationRule(
                id=2,
                name="Invoices & Financial Receipts",
                priority=20,
                enabled=True,
                target_folder="Finances/Invoices",
                condition=RuleCondition(
                    name_pattern="*invoice*",
                    extensions=[".pdf", ".xlsx", ".csv", ".docx"]
                ),
            ),
            OrganizationRule(
                id=3,
                name="Receipts",
                priority=25,
                enabled=True,
                target_folder="Finances/Receipts",
                condition=RuleCondition(
                    name_pattern="*receipt*",
                    extensions=[".pdf", ".jpg", ".png"]
                ),
            ),
            OrganizationRule(
                id=4,
                name="Resumes & CVs",
                priority=30,
                enabled=True,
                target_folder="Career/Resumes",
                condition=RuleCondition(
                    name_pattern="*resume*",
                    extensions=[".pdf", ".docx", ".doc"]
                ),
            ),
            OrganizationRule(
                id=5,
                name="Large Media Files (>100MB)",
                priority=40,
                enabled=True,
                target_folder="Large_Files",
                condition=RuleCondition(
                    min_size_bytes=100 * 1024 * 1024,  # 100 MB
                    extensions=[".mp4", ".mkv", ".mov", ".avi", ".zip", ".iso"]
                ),
            ),
            OrganizationRule(
                id=6,
                name="Software Installers & ISOs",
                priority=50,
                enabled=True,
                target_folder="Software_Installers",
                condition=RuleCondition(
                    extensions=[".exe", ".msi", ".iso", ".dmg", ".appimage"]
                ),
            ),
        ]
        self.sort_rules()
