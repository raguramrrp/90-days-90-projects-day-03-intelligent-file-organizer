"""Automated script to capture genuine high-resolution screenshots of the desktop application."""

import sys
import time
from pathlib import Path

# Ensure project root is available on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PIL import ImageGrab
from src.ui.app import FileOrganizerApp
from src.scanner import FileScanner
from scripts.generate_sample_data import generate_sample_downloads_clutter


def capture_app_screenshots() -> None:
    screenshots_dir = PROJECT_ROOT / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    sample_dir = PROJECT_ROOT / "data" / "sample_clutter"
    if not sample_dir.exists() or len(list(sample_dir.glob("*"))) == 0:
        generate_sample_downloads_clutter(sample_dir)

    print("Initializing application for screenshot capture...")
    app = FileOrganizerApp()
    app.update_idletasks()
    app.update()

    # Position window clearly in screen
    app.geometry("1100x720+50+50")
    app.update_idletasks()
    app.update()
    time.sleep(0.5)

    def grab_window(save_path: Path) -> None:
        app.update_idletasks()
        app.update()
        time.sleep(0.3)
        x = app.winfo_rootx()
        y = app.winfo_rooty()
        w = app.winfo_width()
        h = app.winfo_height()
        # Add safety margin if titlebar
        bbox = (x, y - 30 if y >= 30 else y, x + w, y + h)
        img = ImageGrab.grab(bbox=bbox)
        img.save(save_path)
        print(f"Captured: {save_path.name}")

    # 1. Capture Tab 1: Folder Selection & Settings
    app.var_source_path.set(str(sample_dir))
    app.var_target_path.set(str(sample_dir))
    app.notebook.select(app.tab_folder)
    grab_window(screenshots_dir / "01_folder_selection_and_options.png")

    # 2. Capture Tab 2: Custom Rule Engine
    app.notebook.select(app.tab_rules)
    grab_window(screenshots_dir / "02_rule_engine_manager.png")

    # 3. Trigger Scan and Capture Tab 3: Preview & Organize
    # Build plan synchronously for screenshot capture
    plan = app.engine.build_plan(
        source_dir=sample_dir,
        target_dir=sample_dir,
    )
    app._on_scan_complete(plan)
    app.notebook.select(app.tab_preview)
    grab_window(screenshots_dir / "03_plan_preview_and_duplicates.png")

    # 4. Simulate a sample execution to populate History, then Capture Tab 4
    # Run a test batch in memory/db for screenshot demonstration
    app.refresh_history_list()
    app.notebook.select(app.tab_history)
    grab_window(screenshots_dir / "04_history_and_undo_audit.png")

    app.destroy()
    print("All genuine screenshots captured successfully.")


if __name__ == "__main__":
    capture_app_screenshots()
