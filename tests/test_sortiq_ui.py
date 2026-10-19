"""Unit and integration verification tests for SortIQ desktop application UI."""

import os
import tkinter as tk
from pathlib import Path
import pytest

from src.ui.app import (
    FileOrganizerApp,
    SortIQTheme,
    SortIQPillButton,
    SortIQAnalyticsCanvas,
    NotebookCompatibilityProxy,
)


@pytest.fixture(autouse=True)
def mock_messagebox(monkeypatch):
    """Automatically mock all modal dialogs to avoid hanging in tests."""
    monkeypatch.setattr("tkinter.messagebox.showinfo", lambda *a, **k: None)
    monkeypatch.setattr("tkinter.messagebox.showerror", lambda *a, **k: None)
    monkeypatch.setattr("tkinter.messagebox.showwarning", lambda *a, **k: None)
    monkeypatch.setattr("tkinter.messagebox.askyesno", lambda *a, **k: True)


@pytest.fixture
def app():
    """Create and tear down the FileOrganizerApp headlessly."""
    try:
        app_instance = FileOrganizerApp()
        app_instance.withdraw()
    except tk.TclError:
        pytest.skip("Tkinter display not available in this test environment")

    yield app_instance
    try:
        app_instance.destroy()
    except Exception:
        pass


def test_sortiq_theme_palette():
    """Verify that SortIQTheme contains all brand tokens and required color constants."""
    assert SortIQTheme.BG_ROOT == "#101014"
    assert SortIQTheme.BG_SIDEBAR == "#15151D"
    assert SortIQTheme.BG_CARD == "#1B1B26"
    assert SortIQTheme.ACCENT_PURPLE == "#8B5CF6"
    assert SortIQTheme.ACCENT_VIOLET == "#A78BFA"
    assert SortIQTheme.ACCENT_SUCCESS == "#10B981"
    assert SortIQTheme.ACCENT_WARNING == "#F59E0B"
    assert SortIQTheme.ACCENT_DANGER == "#EF4444"
    assert "Documents" in SortIQTheme.CATEGORY_COLORS
    assert "Images" in SortIQTheme.CATEGORY_COLORS


def test_app_initialization(app):
    """Verify that SortIQ initializes with correct title, navigation views, and KPI cards."""
    assert "SortIQ" in app.title()
    assert app.current_view_key == "dashboard"
    assert app.view_dashboard is not None
    assert app.view_organize is not None
    assert app.view_rules is not None
    assert app.view_preview is not None
    assert app.view_history is not None
    assert app.view_settings is not None
    assert hasattr(app, "kpi_dash_scanned")
    assert hasattr(app, "kpi_dash_organized")
    assert hasattr(app, "kpi_dash_duplicates")
    assert hasattr(app, "kpi_dash_reclaimed")


def test_sidebar_view_switching(app):
    """Verify switching across all 6 navigation views."""
    views = ["dashboard", "organize", "rules", "preview", "history", "settings"]
    for v in views:
        app.switch_view(v)
        assert app.current_view_key == v


def test_notebook_compatibility_proxy(app):
    """Verify backward compatibility proxy for legacy scripts calling app.notebook.select(...)."""
    assert hasattr(app, "notebook")
    app.notebook.select(app.tab_folder)
    assert app.current_view_key == "organize"
    app.notebook.select(app.tab_rules)
    assert app.current_view_key == "rules"
    app.notebook.select(app.tab_preview)
    assert app.current_view_key == "preview"
    app.notebook.select(app.tab_history)
    assert app.current_view_key == "history"
    assert app.notebook.index("end") == 4


def test_analytics_canvas_rendering(app):
    """Verify that SortIQAnalyticsCanvas renders vector slices without errors."""
    canvas = app.dash_analytics_canvas
    test_distribution = {"Documents": 15, "Images": 10, "Code & Scripts": 5}
    canvas.draw_chart(test_distribution)
    assert len(canvas.find_all()) > 0
    # Empty distribution test
    canvas.draw_chart({})
    assert len(canvas.find_all()) > 0


def test_preview_table_filter(app):
    """Verify search filter and quick chips on preview table."""
    app._filter_var.set("invoice")
    app._apply_preview_filter()
    app._filter_var.set("duplicate")
    app._apply_preview_filter()
    app._filter_var.set("")
    app._apply_preview_filter()


def test_plan_population_and_telemetry(app, tmp_path):
    """Verify that build_plan results populate preview table and KPI telemetry without errors."""
    sample_file = tmp_path / "invoice_test.pdf"
    sample_file.write_text("sample content")

    plan = app.engine.build_plan(source_dir=tmp_path, target_dir=tmp_path)
    app._on_scan_complete(plan)

    assert app.current_plan is not None
    assert int(app.kpi_dash_scanned["value"].cget("text")) >= 1
    assert len(app.tree_preview.get_children()) >= 1


def test_rollback_complete_handler(app):
    """Verify that _on_rollback_complete runs cleanly with RollbackResult."""
    from src.engine import RollbackResult
    fake_result = RollbackResult(batch_id="batch-test", restored_count=5, failed_count=0)
    app._on_rollback_complete("batch-test", fake_result)
    assert "batch-test" in app.lbl_status.cget("text")

