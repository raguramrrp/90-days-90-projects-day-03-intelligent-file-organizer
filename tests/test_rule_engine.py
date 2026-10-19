"""Unit tests for user-defined organization rules and pattern evaluation."""

from pathlib import Path
from datetime import datetime, timedelta
import pytest

from src.scanner import FileInfo
from src.rules import OrganizationRule, RuleCondition, RuleEngine


def make_file(name: str, ext: str, size: int = 1024, days_old: int = 5) -> FileInfo:
    now = datetime.now()
    mod_time = now - timedelta(days=days_old)
    return FileInfo(
        path=Path(f"/mock/{name}"),
        name=name,
        stem=name[:-len(ext)] if ext else name,
        extension=ext,
        size_bytes=size,
        created_at=mod_time,
        modified_at=mod_time,
        is_hidden=False,
        is_symlink=False,
    )


def test_rule_wildcard_matching() -> None:
    rule = OrganizationRule(
        name="Invoice Rule",
        target_folder="Finances/Invoices",
        priority=10,
        condition=RuleCondition(name_pattern="*invoice*"),
    )
    match_file = make_file("monthly_invoice_oct.pdf", ".pdf")
    non_match_file = make_file("random_document.pdf", ".pdf")

    assert rule.matches(match_file) is True
    assert rule.matches(non_match_file) is False


def test_rule_regex_matching() -> None:
    rule = OrganizationRule(
        name="Screenshot Regex",
        target_folder="Screenshots",
        priority=10,
        condition=RuleCondition(name_pattern=r"regex:^IMG_\d{4}\.png$"),
    )
    assert rule.matches(make_file("IMG_2026.png", ".png")) is True
    assert rule.matches(make_file("IMG_ABC.png", ".png")) is False


def test_rule_size_constraints() -> None:
    rule = OrganizationRule(
        name="Large Files",
        target_folder="Large_Files",
        priority=20,
        condition=RuleCondition(min_size_bytes=50 * 1024 * 1024),  # 50 MB
    )
    small_file = make_file("small.zip", ".zip", size=10 * 1024 * 1024)
    big_file = make_file("large.iso", ".iso", size=100 * 1024 * 1024)

    assert rule.matches(small_file) is False
    assert rule.matches(big_file) is True


def test_rule_engine_priority_resolution() -> None:
    rule_high = OrganizationRule(
        id=1,
        name="Urgent Invoices",
        target_folder="Urgent_Invoices",
        priority=5,
        condition=RuleCondition(name_pattern="*urgent*"),
    )
    rule_normal = OrganizationRule(
        id=2,
        name="All Invoices",
        target_folder="General_Invoices",
        priority=20,
        condition=RuleCondition(name_pattern="*invoice*"),
    )

    engine = RuleEngine([rule_normal, rule_high])  # Provided out of order
    assert engine.rules[0].name == "Urgent Invoices"
    assert engine.rules[1].name == "All Invoices"

    target_urgent = make_file("urgent_invoice_oct.pdf", ".pdf")
    match = engine.evaluate(target_urgent)
    assert match is not None
    matched_rule, folder = match
    assert matched_rule.name == "Urgent Invoices"
    assert folder == Path("Urgent_Invoices")


def test_rule_serialization_roundtrip() -> None:
    rule = OrganizationRule(
        id=42,
        name="Test Rule",
        target_folder="Test_Folder",
        priority=15,
        enabled=True,
        condition=RuleCondition(
            name_pattern="*test*",
            extensions=[".pdf", ".txt"],
            min_size_bytes=100,
            max_size_bytes=10000,
        ),
    )
    as_dict = rule.to_dict()
    restored = OrganizationRule.from_dict(as_dict)
    assert restored.name == rule.name
    assert restored.priority == rule.priority
    assert restored.condition.extensions == [".pdf", ".txt"]
    assert restored.condition.min_size_bytes == 100
