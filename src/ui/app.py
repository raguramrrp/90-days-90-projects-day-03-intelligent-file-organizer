"""Modern Tkinter graphical user interface for desktop file organization automation."""

from __future__ import annotations

import os
import sys
import subprocess
import threading
from pathlib import Path
from typing import Optional, List, Dict, Any

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from src.scanner import FileScanner, format_bytes
from src.classifier import DateGroupingMode, HierarchyStyle
from src.rules import OrganizationRule, RuleCondition, RuleEngine
from src.duplicates import DuplicateStrategy
from src.engine import (
    OrganizerEngine,
    OrganizationPlan,
    PlannedAction,
    ActionType,
    ConflictStrategy,
    ExecutionResult,
)


class ModernTheme:
    """Design palette and font configuration for clean presentation."""
    BG_DARK = "#1e1e2e"
    BG_PANEL = "#252538"
    BG_CARD = "#2b2b40"
    FG_LIGHT = "#cdd6f4"
    FG_MUTED = "#a6adc8"
    ACCENT_PRIMARY = "#89b4fa"      # Soft Sky Blue
    ACCENT_SUCCESS = "#a6e3a1"      # Mint Green
    ACCENT_WARNING = "#f9e2af"      # Amber
    ACCENT_DANGER = "#f38ba8"       # Rose Red
    FONT_FAMILY = "Segoe UI" if sys.platform == "win32" else "Helvetica"


class RuleDialog(tk.Toplevel):
    """Modal dialog for creating or updating an organization rule."""

    def __init__(
        self,
        parent: tk.Tk | tk.Toplevel,
        rule: Optional[OrganizationRule] = None,
        title: str = "Add Organization Rule",
    ) -> None:
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.result: Optional[OrganizationRule] = None
        self.existing_rule = rule

        self._build_ui()
        self._populate_fields()
        self.geometry("520x560")
        self.center_window()

    def center_window(self) -> None:
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (520 // 2)
        y = (self.winfo_screenheight() // 2) - (560 // 2)
        self.geometry(f"+{x}+{y}")

    def _build_ui(self) -> None:
        pad = {"padx": 16, "pady": 6}

        header_frame = ttk.Frame(self)
        header_frame.pack(fill="x", padx=16, pady=(16, 8))
        ttk.Label(
            header_frame,
            text="Configure Rule Criteria",
            font=(ModernTheme.FONT_FAMILY, 13, "bold")
        ).pack(anchor="w")
        ttk.Label(
            header_frame,
            text="Matches apply in priority order. All specified conditions must be satisfied.",
            font=(ModernTheme.FONT_FAMILY, 9)
        ).pack(anchor="w")

        form = ttk.Frame(self)
        form.pack(fill="both", expand=True, padx=16, pady=8)

        # Rule Name
        ttk.Label(form, text="Rule Name: *").grid(row=0, column=0, sticky="w", **pad)
        self.var_name = tk.StringVar()
        ttk.Entry(form, textvariable=self.var_name, width=36).grid(row=0, column=1, sticky="w", **pad)

        # Target Folder
        ttk.Label(form, text="Target Subfolder: *").grid(row=1, column=0, sticky="w", **pad)
        self.var_target = tk.StringVar()
        ttk.Entry(form, textvariable=self.var_target, width=36).grid(row=1, column=1, sticky="w", **pad)

        # Priority
        ttk.Label(form, text="Priority (1 = Highest):").grid(row=2, column=0, sticky="w", **pad)
        self.var_priority = tk.IntVar(value=100)
        ttk.Spinbox(form, from_=1, to=999, textvariable=self.var_priority, width=12).grid(row=2, column=1, sticky="w", **pad)

        # Name Pattern
        ttk.Label(form, text="File Name Pattern:").grid(row=3, column=0, sticky="w", **pad)
        self.var_pattern = tk.StringVar()
        ttk.Entry(form, textvariable=self.var_pattern, width=36).grid(row=3, column=1, sticky="w", **pad)
        ttk.Label(form, text="e.g. *invoice*, receipt*, regex:^IMG_\\d+", font=(ModernTheme.FONT_FAMILY, 8)).grid(row=4, column=1, sticky="w", padx=16)

        # Extensions
        ttk.Label(form, text="File Extensions:").grid(row=5, column=0, sticky="w", **pad)
        self.var_extensions = tk.StringVar()
        ttk.Entry(form, textvariable=self.var_extensions, width=36).grid(row=5, column=1, sticky="w", **pad)
        ttk.Label(form, text="Comma separated: .pdf, .xlsx, .docx", font=(ModernTheme.FONT_FAMILY, 8)).grid(row=6, column=1, sticky="w", padx=16)

        # Min Size (MB)
        ttk.Label(form, text="Min Size (MB):").grid(row=7, column=0, sticky="w", **pad)
        self.var_min_size = tk.StringVar()
        ttk.Entry(form, textvariable=self.var_min_size, width=12).grid(row=7, column=1, sticky="w", **pad)

        # Max Size (MB)
        ttk.Label(form, text="Max Size (MB):").grid(row=8, column=0, sticky="w", **pad)
        self.var_max_size = tk.StringVar()
        ttk.Entry(form, textvariable=self.var_max_size, width=12).grid(row=8, column=1, sticky="w", **pad)

        # Enabled checkbox
        self.var_enabled = tk.BooleanVar(value=True)
        ttk.Checkbutton(form, text="Rule Active / Enabled", variable=self.var_enabled).grid(row=9, column=1, sticky="w", **pad)

        # Action Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=16, pady=16)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side="right", padx=6)
        ttk.Button(btn_frame, text="Save Rule", command=self._on_save).pack(side="right", padx=6)

    def _populate_fields(self) -> None:
        if not self.existing_rule:
            return
        r = self.existing_rule
        self.var_name.set(r.name)
        self.var_target.set(r.target_folder)
        self.var_priority.set(r.priority)
        self.var_enabled.set(r.enabled)

        cond = r.condition
        if cond.name_pattern:
            self.var_pattern.set(cond.name_pattern)
        if cond.extensions:
            self.var_extensions.set(", ".join(cond.extensions))
        if cond.min_size_bytes is not None:
            self.var_min_size.set(str(round(cond.min_size_bytes / (1024 * 1024), 2)))
        if cond.max_size_bytes is not None:
            self.var_max_size.set(str(round(cond.max_size_bytes / (1024 * 1024), 2)))

    def _on_save(self) -> None:
        name = self.var_name.get().strip()
        target = self.var_target.get().strip()

        if not name or not target:
            messagebox.showwarning("Validation Error", "Rule Name and Target Folder are required fields.", parent=self)
            return

        # Parse extensions
        raw_ext = self.var_extensions.get().strip()
        extensions = None
        if raw_ext:
            extensions = [
                ext.strip() if ext.strip().startswith(".") else f".{ext.strip()}"
                for ext in raw_ext.split(",")
                if ext.strip()
            ]

        # Parse sizes
        min_bytes = None
        if self.var_min_size.get().strip():
            try:
                min_bytes = int(float(self.var_min_size.get().strip()) * 1024 * 1024)
            except ValueError:
                messagebox.showerror("Error", "Invalid Min Size value.", parent=self)
                return

        max_bytes = None
        if self.var_max_size.get().strip():
            try:
                max_bytes = int(float(self.var_max_size.get().strip()) * 1024 * 1024)
            except ValueError:
                messagebox.showerror("Error", "Invalid Max Size value.", parent=self)
                return

        pattern = self.var_pattern.get().strip() or None

        condition = RuleCondition(
            name_pattern=pattern,
            extensions=extensions,
            min_size_bytes=min_bytes,
            max_size_bytes=max_bytes,
        )

        self.result = OrganizationRule(
            id=self.existing_rule.id if self.existing_rule else None,
            name=name,
            target_folder=target,
            priority=self.var_priority.get(),
            enabled=self.var_enabled.get(),
            condition=condition,
        )
        self.destroy()


class FileOrganizerApp(tk.Tk):
    """Main desktop automation window for file organization."""

    def __init__(self, engine: Optional[OrganizerEngine] = None) -> None:
        super().__init__()
        self.title("Context-Aware Desktop File Organizer")
        self.geometry("1100x720")
        self.minsize(960, 600)

        self.engine = engine or OrganizerEngine()
        self.current_plan: Optional[OrganizationPlan] = None
        self._filter_var = tk.StringVar()

        self._configure_styles()
        self._build_header()
        self._build_tabs()
        self._build_status_bar()

        # Set default scan path to Downloads folder
        default_dir = FileScanner.get_default_downloads_folder()
        self.var_source_path.set(str(default_dir))
        self.var_target_path.set(str(default_dir))

        self.refresh_rules_list()
        self.refresh_history_list()

    def _configure_styles(self) -> None:
        """Configure theme styles for clean modern widgets."""
        self.style = ttk.Style(self)
        # Attempt to use 'clam' or native theme as base
        available_themes = self.style.theme_names()
        if "clam" in available_themes:
            self.style.theme_use("clam")

        self.style.configure(".", font=(ModernTheme.FONT_FAMILY, 9))
        self.style.configure("Header.TLabel", font=(ModernTheme.FONT_FAMILY, 15, "bold"))
        self.style.configure("SubHeader.TLabel", font=(ModernTheme.FONT_FAMILY, 9))
        self.style.configure("Card.TFrame", relief="solid", borderwidth=1)
        self.style.configure("CardTitle.TLabel", font=(ModernTheme.FONT_FAMILY, 9, "bold"))
        self.style.configure("CardValue.TLabel", font=(ModernTheme.FONT_FAMILY, 14, "bold"))
        self.style.configure("Accent.TButton", font=(ModernTheme.FONT_FAMILY, 9, "bold"))
        self.style.configure("Treeview.Heading", font=(ModernTheme.FONT_FAMILY, 9, "bold"))

    def _build_header(self) -> None:
        """Top banner card with branding and summary metrics."""
        header = ttk.Frame(self, padding=(16, 12, 16, 8))
        header.pack(fill="x")

        title_frame = ttk.Frame(header)
        title_frame.pack(side="left")

        ttk.Label(
            title_frame,
            text="📂 Context-Aware Desktop File Organizer",
            style="Header.TLabel"
        ).pack(anchor="w")

        ttk.Label(
            title_frame,
            text="Automated file classification, duplicate detection, rule evaluation, and reversible audit history.",
            style="SubHeader.TLabel"
        ).pack(anchor="w")

        stats_frame = ttk.Frame(header)
        stats_frame.pack(side="right")

        stats = self.engine.db.get_stats()
        self._lbl_total_moved = ttk.Label(
            stats_frame,
            text=f"Total Files Organized: {stats['total_files_moved']} | Batches: {stats['total_batches']}",
            font=(ModernTheme.FONT_FAMILY, 9, "italic")
        )
        self._lbl_total_moved.pack(anchor="e")

    def _build_tabs(self) -> None:
        """Build the four core tab panels."""
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=12, pady=(0, 6))

        # Tab 1: Folder Selection & Settings
        self.tab_folder = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(self.tab_folder, text="  1. Folder & Options  ")
        self._init_tab_folder()

        # Tab 2: Custom Rules Engine
        self.tab_rules = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(self.tab_rules, text="  2. Rule Engine  ")
        self._init_tab_rules()

        # Tab 3: Plan Preview & Execution
        self.tab_preview = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(self.tab_preview, text="  3. Preview & Organize  ")
        self._init_tab_preview()

        # Tab 4: History & Rollback Audit
        self.tab_history = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(self.tab_history, text="  4. History & Undo  ")
        self._init_tab_history()

    def _build_status_bar(self) -> None:
        """Bottom status indicator and progress bar."""
        bar = ttk.Frame(self, padding=(12, 4))
        bar.pack(fill="x", side="bottom")

        self.lbl_status = ttk.Label(bar, text="Ready.", font=(ModernTheme.FONT_FAMILY, 9))
        self.lbl_status.pack(side="left")

        self.progress_bar = ttk.Progressbar(bar, orient="horizontal", mode="determinate", length=240)
        self.progress_bar.pack(side="right", padx=6)

    # =========================================================================
    # TAB 1: Folder Selection & Configuration
    # =========================================================================

    def _init_tab_folder(self) -> None:
        # Directory Selectors
        dir_group = ttk.LabelFrame(self.tab_folder, text="Folder Locations", padding=12)
        dir_group.pack(fill="x", pady=6)

        # Source Directory
        ttk.Label(dir_group, text="Source Folder (to organize):").grid(row=0, column=0, sticky="w", pady=4)
        self.var_source_path = tk.StringVar()
        ttk.Entry(dir_group, textvariable=self.var_source_path, width=64).grid(row=0, column=1, sticky="we", padx=8, pady=4)
        ttk.Button(dir_group, text="Browse...", command=self._browse_source).grid(row=0, column=2, padx=4, pady=4)
        ttk.Button(dir_group, text="Downloads", command=self._set_source_downloads).grid(row=0, column=3, padx=4, pady=4)

        # Target Directory
        ttk.Label(dir_group, text="Destination Folder:").grid(row=1, column=0, sticky="w", pady=4)
        self.var_target_path = tk.StringVar()
        ttk.Entry(dir_group, textvariable=self.var_target_path, width=64).grid(row=1, column=1, sticky="we", padx=8, pady=4)
        ttk.Button(dir_group, text="Browse...", command=self._browse_target).grid(row=1, column=2, padx=4, pady=4)
        ttk.Button(dir_group, text="Same as Source", command=self._set_target_same).grid(row=1, column=3, padx=4, pady=4)

        dir_group.columnconfigure(1, weight=1)

        # Strategy and Behavior Options
        opt_group = ttk.LabelFrame(self.tab_folder, text="Organization Strategies & Rules", padding=12)
        opt_group.pack(fill="x", pady=6)

        # Date Grouping
        ttk.Label(opt_group, text="Date Sub-folders:").grid(row=0, column=0, sticky="w", pady=6, padx=6)
        self.var_date_mode = tk.StringVar(value=DateGroupingMode.NONE.value)
        cbo_date = ttk.Combobox(
            opt_group,
            textvariable=self.var_date_mode,
            values=[m.value for m in DateGroupingMode],
            state="readonly",
            width=16
        )
        cbo_date.grid(row=0, column=1, sticky="w", pady=6, padx=6)

        # Hierarchy Style
        ttk.Label(opt_group, text="Directory Layout:").grid(row=0, column=2, sticky="w", pady=6, padx=6)
        self.var_hierarchy = tk.StringVar(value=HierarchyStyle.CATEGORY_FIRST.value)
        cbo_hier = ttk.Combobox(
            opt_group,
            textvariable=self.var_hierarchy,
            values=[h.value for h in HierarchyStyle],
            state="readonly",
            width=18
        )
        cbo_hier.grid(row=0, column=3, sticky="w", pady=6, padx=6)

        # Conflict Resolution
        ttk.Label(opt_group, text="Filename Collisions:").grid(row=1, column=0, sticky="w", pady=6, padx=6)
        self.var_conflict = tk.StringVar(value=ConflictStrategy.RENAME.value)
        cbo_conflict = ttk.Combobox(
            opt_group,
            textvariable=self.var_conflict,
            values=[c.value for c in ConflictStrategy],
            state="readonly",
            width=16
        )
        cbo_conflict.grid(row=1, column=1, sticky="w", pady=6, padx=6)

        # Duplicate Handling
        ttk.Label(opt_group, text="Duplicate Handling:").grid(row=1, column=2, sticky="w", pady=6, padx=6)
        self.var_duplicate = tk.StringVar(value=DuplicateStrategy.REPORT_ONLY.value)
        cbo_dup = ttk.Combobox(
            opt_group,
            textvariable=self.var_duplicate,
            values=[d.value for d in DuplicateStrategy],
            state="readonly",
            width=18
        )
        cbo_dup.grid(row=1, column=3, sticky="w", pady=6, padx=6)

        # Checkboxes
        check_frame = ttk.Frame(opt_group)
        check_frame.grid(row=2, column=0, columnspan=4, sticky="w", pady=(8, 4))
        self.var_recursive = tk.BooleanVar(value=False)
        ttk.Checkbutton(check_frame, text="Recursive Scan (traverse subfolders)", variable=self.var_recursive).pack(side="left", padx=8)
        self.var_hidden = tk.BooleanVar(value=False)
        ttk.Checkbutton(check_frame, text="Include Hidden Files", variable=self.var_hidden).pack(side="left", padx=8)

        # Scan Button
        action_bar = ttk.Frame(self.tab_folder, padding=8)
        action_bar.pack(fill="x", pady=12)

        self.btn_scan = ttk.Button(
            action_bar,
            text="🔍 Scan Folder & Generate Organization Preview",
            style="Accent.TButton",
            command=self._start_scan_async
        )
        self.btn_scan.pack(side="left", padx=6, ipady=4)

        ttk.Button(
            action_bar,
            text="📁 Open Source in Explorer",
            command=self._open_source_explorer
        ).pack(side="left", padx=6, ipady=4)

        # Instruction Guide Note
        note_box = ttk.LabelFrame(self.tab_folder, text="How It Works", padding=12)
        note_box.pack(fill="both", expand=True, pady=6)
        workflow_text = (
            "1. Select the messy folder you wish to tidy (e.g. your Downloads or Desktop).\n"
            "2. Configure date grouping and conflict preferences.\n"
            "3. Click 'Scan Folder & Generate Preview' to simulate the moves safely.\n"
            "4. Review the generated plan in the Preview tab and click 'Execute Organization'.\n"
            "5. If needed, you can fully reverse any batch at any time in the 'History & Undo' tab!"
        )
        ttk.Label(note_box, text=workflow_text, font=(ModernTheme.FONT_FAMILY, 9), justify="left").pack(anchor="w")

    def _browse_source(self) -> None:
        chosen = filedialog.askdirectory(title="Select Folder to Organize", initialdir=self.var_source_path.get())
        if chosen:
            self.var_source_path.set(chosen)
            if not self.var_target_path.get():
                self.var_target_path.set(chosen)

    def _browse_target(self) -> None:
        chosen = filedialog.askdirectory(title="Select Destination Folder", initialdir=self.var_target_path.get())
        if chosen:
            self.var_target_path.set(chosen)

    def _set_source_downloads(self) -> None:
        downloads = FileScanner.get_default_downloads_folder()
        self.var_source_path.set(str(downloads))
        self.var_target_path.set(str(downloads))

    def _set_target_same(self) -> None:
        self.var_target_path.set(self.var_source_path.get())

    def _open_source_explorer(self) -> None:
        p = Path(self.var_source_path.get())
        if p.exists():
            if sys.platform == "win32":
                os.startfile(str(p))
            else:
                subprocess.run(["xdg-open", str(p)])
        else:
            messagebox.showwarning("Notice", "Selected source folder does not exist.")

    # =========================================================================
    # TAB 2: Rule Engine Management
    # =========================================================================

    def _init_tab_rules(self) -> None:
        desc_frame = ttk.Frame(self.tab_rules)
        desc_frame.pack(fill="x", pady=(0, 8))
        ttk.Label(
            desc_frame,
            text="Active Categorization Rules (Evaluated in Priority Order):",
            font=(ModernTheme.FONT_FAMILY, 10, "bold")
        ).pack(side="left")

        # Treeview for Rules
        cols = ("Priority", "Name", "Target Folder", "Pattern", "Extensions", "Size/Age", "Status")
        self.tree_rules = ttk.Treeview(self.tab_rules, columns=cols, show="headings", height=12)
        
        self.tree_rules.heading("Priority", text="Priority", anchor="center")
        self.tree_rules.heading("Name", text="Rule Name", anchor="w")
        self.tree_rules.heading("Target Folder", text="Destination Subfolder", anchor="w")
        self.tree_rules.heading("Pattern", text="Name Pattern", anchor="w")
        self.tree_rules.heading("Extensions", text="Extensions", anchor="w")
        self.tree_rules.heading("Size/Age", text="Size Filter", anchor="center")
        self.tree_rules.heading("Status", text="Status", anchor="center")

        self.tree_rules.column("Priority", width=70, anchor="center")
        self.tree_rules.column("Name", width=180, anchor="w")
        self.tree_rules.column("Target Folder", width=160, anchor="w")
        self.tree_rules.column("Pattern", width=140, anchor="w")
        self.tree_rules.column("Extensions", width=140, anchor="w")
        self.tree_rules.column("Size/Age", width=110, anchor="center")
        self.tree_rules.column("Status", width=90, anchor="center")

        scroll_y = ttk.Scrollbar(self.tab_rules, orient="vertical", command=self.tree_rules.yview)
        self.tree_rules.configure(yscrollcommand=scroll_y.set)

        self.tree_rules.pack(side="top", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y", in_=self.tab_rules)

        # Rule Action Buttons
        btn_bar = ttk.Frame(self.tab_rules, padding=(0, 10))
        btn_bar.pack(fill="x")

        ttk.Button(btn_bar, text="➕ Add Rule", command=self._add_rule).pack(side="left", padx=4)
        ttk.Button(btn_bar, text="✏️ Edit Selected", command=self._edit_rule).pack(side="left", padx=4)
        ttk.Button(btn_bar, text="🗑️ Delete Selected", command=self._delete_rule).pack(side="left", padx=4)
        ttk.Button(btn_bar, text="🔄 Toggle Enabled", command=self._toggle_rule).pack(side="left", padx=4)
        ttk.Button(btn_bar, text="↺ Reset Defaults", command=self._reset_default_rules).pack(side="right", padx=4)

    def refresh_rules_list(self) -> None:
        """Reload and display active rules from the database."""
        for item in self.tree_rules.get_children():
            self.tree_rules.delete(item)

        rules = self.engine.db.load_rules()
        if not rules:
            self.engine.db.initialize_default_rules_if_empty(self.engine.rules.rules)
            rules = self.engine.db.load_rules()

        self.engine.rules = RuleEngine(rules)

        for rule in rules:
            cond = rule.condition
            pat = cond.name_pattern or "-"
            exts = ", ".join(cond.extensions) if cond.extensions else "Any"
            size_txt = "-"
            if cond.min_size_bytes is not None:
                size_txt = f"> {format_bytes(cond.min_size_bytes)}"
            elif cond.max_size_bytes is not None:
                size_txt = f"< {format_bytes(cond.max_size_bytes)}"

            status_txt = "Active ✓" if rule.enabled else "Disabled"

            self.tree_rules.insert(
                "",
                "end",
                iid=str(rule.id),
                values=(
                    rule.priority,
                    rule.name,
                    rule.target_folder,
                    pat,
                    exts,
                    size_txt,
                    status_txt,
                )
            )

    def _add_rule(self) -> None:
        dlg = RuleDialog(self, title="Add Organization Rule")
        self.wait_window(dlg)
        if dlg.result:
            self.engine.db.save_rule(dlg.result)
            self.refresh_rules_list()
            self.set_status(f"Added rule: {dlg.result.name}")

    def _edit_rule(self) -> None:
        selected = self.tree_rules.selection()
        if not selected:
            messagebox.showinfo("Select Rule", "Please select a rule to edit.")
            return
        rule_id = int(selected[0])
        rules = self.engine.db.load_rules()
        matched = next((r for r in rules if r.id == rule_id), None)
        if matched:
            dlg = RuleDialog(self, rule=matched, title=f"Edit Rule: {matched.name}")
            self.wait_window(dlg)
            if dlg.result:
                self.engine.db.save_rule(dlg.result)
                self.refresh_rules_list()
                self.set_status(f"Updated rule: {dlg.result.name}")

    def _delete_rule(self) -> None:
        selected = self.tree_rules.selection()
        if not selected:
            messagebox.showinfo("Select Rule", "Please select a rule to delete.")
            return
        rule_id = int(selected[0])
        if messagebox.askyesno("Confirm Deletion", "Are you sure you want to delete this rule?"):
            self.engine.db.delete_rule(rule_id)
            self.refresh_rules_list()
            self.set_status("Rule deleted.")

    def _toggle_rule(self) -> None:
        selected = self.tree_rules.selection()
        if not selected:
            return
        rule_id = int(selected[0])
        rules = self.engine.db.load_rules()
        matched = next((r for r in rules if r.id == rule_id), None)
        if matched:
            matched.enabled = not matched.enabled
            self.engine.db.save_rule(matched)
            self.refresh_rules_list()
            self.set_status(f"Rule '{matched.name}' status toggled.")

    def _reset_default_rules(self) -> None:
        if messagebox.askyesno("Reset Rules", "Reset all rules back to default presets? Custom rules will be replaced."):
            fresh_engine = RuleEngine()
            # Clear DB rules table
            with self.engine.db.get_connection() as conn:
                conn.execute("DELETE FROM rules;")
                conn.commit()
            self.engine.db.initialize_default_rules_if_empty(fresh_engine.rules)
            self.refresh_rules_list()
            self.set_status("Reset rules to default configuration.")

    # =========================================================================
    # TAB 3: Plan Preview & Execution
    # =========================================================================

    def _init_tab_preview(self) -> None:
        # Metrics KPI banner
        kpi_frame = ttk.Frame(self.tab_preview)
        kpi_frame.pack(fill="x", pady=(0, 8))

        self.kpi_files = ttk.Label(kpi_frame, text="Files Scanned: 0", font=(ModernTheme.FONT_FAMILY, 9, "bold"))
        self.kpi_files.pack(side="left", padx=8)

        self.kpi_moves = ttk.Label(kpi_frame, text="Files to Move: 0", font=(ModernTheme.FONT_FAMILY, 9, "bold"))
        self.kpi_moves.pack(side="left", padx=8)

        self.kpi_dups = ttk.Label(kpi_frame, text="Duplicates: 0", font=(ModernTheme.FONT_FAMILY, 9, "bold"))
        self.kpi_dups.pack(side="left", padx=8)

        self.kpi_space = ttk.Label(kpi_frame, text="Wasted Space: 0 B", font=(ModernTheme.FONT_FAMILY, 9, "bold"))
        self.kpi_space.pack(side="left", padx=8)

        # Filter and Search Bar
        filter_bar = ttk.Frame(self.tab_preview)
        filter_bar.pack(fill="x", pady=(0, 6))

        ttk.Label(filter_bar, text="Filter Preview:").pack(side="left", padx=(4, 6))
        entry_filter = ttk.Entry(filter_bar, textvariable=self._filter_var, width=28)
        entry_filter.pack(side="left", padx=4)
        entry_filter.bind("<KeyRelease>", lambda e: self._apply_preview_filter())

        ttk.Button(filter_bar, text="Clear Filter", command=lambda: [self._filter_var.set(""), self._apply_preview_filter()]).pack(side="left", padx=4)
        ttk.Button(filter_bar, text="Select All", command=lambda: self._set_all_included(True)).pack(side="left", padx=8)
        ttk.Button(filter_bar, text="Deselect All", command=lambda: self._set_all_included(False)).pack(side="left", padx=4)

        # Preview Treeview
        cols = ("Include", "Source File", "Destination Folder", "Category / Rule", "Action", "Size", "Duplicate")
        self.tree_preview = ttk.Treeview(self.tab_preview, columns=cols, show="headings", height=14)

        self.tree_preview.heading("Include", text="[✓]", anchor="center")
        self.tree_preview.heading("Source File", text="Source File Name", anchor="w")
        self.tree_preview.heading("Destination Folder", text="Destination Path", anchor="w")
        self.tree_preview.heading("Category / Rule", text="Matched Category / Rule", anchor="w")
        self.tree_preview.heading("Action", text="Action", anchor="center")
        self.tree_preview.heading("Size", text="Size", anchor="e")
        self.tree_preview.heading("Duplicate", text="Duplicate?", anchor="center")

        self.tree_preview.column("Include", width=45, anchor="center")
        self.tree_preview.column("Source File", width=220, anchor="w")
        self.tree_preview.column("Destination Folder", width=240, anchor="w")
        self.tree_preview.column("Category / Rule", width=170, anchor="w")
        self.tree_preview.column("Action", width=120, anchor="center")
        self.tree_preview.column("Size", width=80, anchor="e")
        self.tree_preview.column("Duplicate", width=90, anchor="center")

        # Double-click to toggle inclusion
        self.tree_preview.bind("<Double-1>", self._on_preview_double_click)

        scroll_preview = ttk.Scrollbar(self.tab_preview, orient="vertical", command=self.tree_preview.yview)
        self.tree_preview.configure(yscrollcommand=scroll_preview.set)

        self.tree_preview.pack(side="top", fill="both", expand=True)
        scroll_preview.pack(side="right", fill="y", in_=self.tab_preview)

        # Bottom Execution Toolbar
        exec_bar = ttk.Frame(self.tab_preview, padding=(0, 10))
        exec_bar.pack(fill="x")

        self.btn_execute = ttk.Button(
            exec_bar,
            text="🚀 Execute Organization Now",
            style="Accent.TButton",
            command=self._execute_plan_async,
            state="disabled"
        )
        self.btn_execute.pack(side="left", padx=6, ipady=4)

        ttk.Button(
            exec_bar,
            text="Toggle Selected Item [✓]",
            command=self._toggle_selected_preview
        ).pack(side="left", padx=6)

    def _on_preview_double_click(self, event: Any) -> None:
        self._toggle_selected_preview()

    def _toggle_selected_preview(self) -> None:
        selected = self.tree_preview.selection()
        if not selected or not self.current_plan:
            return
        for item_id in selected:
            idx = int(item_id)
            if 0 <= idx < len(self.current_plan.actions):
                action = self.current_plan.actions[idx]
                action.included = not action.included
        self._apply_preview_filter()
        self._update_kpi_metrics()

    def _set_all_included(self, state: bool) -> None:
        if not self.current_plan:
            return
        for action in self.current_plan.actions:
            if action.action_type != ActionType.SKIP:
                action.included = state
        self._apply_preview_filter()
        self._update_kpi_metrics()

    def _update_kpi_metrics(self) -> None:
        if not self.current_plan:
            return
        p = self.current_plan
        self.kpi_files.config(text=f"Files Scanned: {p.total_files}")
        self.kpi_moves.config(text=f"Files to Move: {p.files_to_move}")
        self.kpi_dups.config(text=f"Duplicates: {p.duplicate_report.total_duplicates}")
        self.kpi_space.config(text=f"Wasted Space: {p.duplicate_report.readable_wasted_space}")
        self.btn_execute.config(state="normal" if p.files_to_move > 0 else "disabled")

    def _apply_preview_filter(self) -> None:
        """Render rows matching search filter."""
        for item in self.tree_preview.get_children():
            self.tree_preview.delete(item)

        if not self.current_plan:
            return

        query = self._filter_var.get().strip().lower()

        for idx, a in enumerate(self.current_plan.actions):
            # Check filter query
            if query:
                match = (
                    query in a.source_name.lower() or
                    query in str(a.relative_dest).lower() or
                    query in a.category.lower() or
                    query in a.action_type.value.lower()
                )
                if not match:
                    continue

            inc_symbol = "☑" if a.included else "☐"
            dup_symbol = "Duplicate" if a.is_duplicate else "-"

            self.tree_preview.insert(
                "",
                "end",
                iid=str(idx),
                values=(
                    inc_symbol,
                    a.source_name,
                    str(a.relative_dest),
                    a.category,
                    a.action_type.value,
                    a.size_readable,
                    dup_symbol,
                )
            )

    # =========================================================================
    # TAB 4: History & Rollback Audit Logs
    # =========================================================================

    def _init_tab_history(self) -> None:
        header_bar = ttk.Frame(self.tab_history)
        header_bar.pack(fill="x", pady=(0, 8))

        ttk.Label(
            header_bar,
            text="Organization Audit Batches & Rollback History:",
            font=(ModernTheme.FONT_FAMILY, 10, "bold")
        ).pack(side="left")

        ttk.Button(header_bar, text="🔄 Refresh History", command=self.refresh_history_list).pack(side="right", padx=4)

        # Batch List Treeview
        cols = ("Batch ID", "Created At", "Source Folder", "Total", "Moved", "Skipped", "Status")
        self.tree_history = ttk.Treeview(self.tab_history, columns=cols, show="headings", height=8)

        self.tree_history.heading("Batch ID", text="Batch ID", anchor="w")
        self.tree_history.heading("Created At", text="Timestamp", anchor="center")
        self.tree_history.heading("Source Folder", text="Source Directory", anchor="w")
        self.tree_history.heading("Total", text="Total", anchor="center")
        self.tree_history.heading("Moved", text="Moved", anchor="center")
        self.tree_history.heading("Skipped", text="Skipped", anchor="center")
        self.tree_history.heading("Status", text="Status", anchor="center")

        self.tree_history.column("Batch ID", width=180, anchor="w")
        self.tree_history.column("Created At", width=140, anchor="center")
        self.tree_history.column("Source Folder", width=260, anchor="w")
        self.tree_history.column("Total", width=60, anchor="center")
        self.tree_history.column("Moved", width=60, anchor="center")
        self.tree_history.column("Skipped", width=60, anchor="center")
        self.tree_history.column("Status", width=100, anchor="center")

        self.tree_history.bind("<<TreeviewSelect>>", self._on_history_batch_selected)

        self.tree_history.pack(fill="x", pady=4)

        # Sub-view: Operations inside selected batch
        ttk.Label(
            self.tab_history,
            text="Files in Selected Batch:",
            font=(ModernTheme.FONT_FAMILY, 9, "bold")
        ).pack(anchor="w", pady=(8, 2))

        sub_cols = ("Source Path", "Destination Path", "Size", "Status", "Rule / Note")
        self.tree_ops = ttk.Treeview(self.tab_history, columns=sub_cols, show="headings", height=7)
        self.tree_ops.heading("Source Path", text="Original Source Path", anchor="w")
        self.tree_ops.heading("Destination Path", text="Destination Path", anchor="w")
        self.tree_ops.heading("Size", text="Size", anchor="e")
        self.tree_ops.heading("Status", text="Status", anchor="center")
        self.tree_ops.heading("Rule / Note", text="Rule Applied", anchor="w")

        self.tree_ops.column("Source Path", width=280, anchor="w")
        self.tree_ops.column("Destination Path", width=280, anchor="w")
        self.tree_ops.column("Size", width=80, anchor="e")
        self.tree_ops.column("Status", width=90, anchor="center")
        self.tree_ops.column("Rule / Note", width=140, anchor="w")

        self.tree_ops.pack(fill="both", expand=True, pady=4)

        # History Toolbar
        hist_bar = ttk.Frame(self.tab_history, padding=(0, 6))
        hist_bar.pack(fill="x")

        self.btn_undo = ttk.Button(
            hist_bar,
            text="↩️ Undo / Rollback Selected Batch",
            style="Accent.TButton",
            command=self._rollback_selected_batch,
            state="disabled"
        )
        self.btn_undo.pack(side="left", padx=4)

        ttk.Button(hist_bar, text="📥 Export CSV Audit Log", command=self._export_csv).pack(side="right", padx=4)
        ttk.Button(hist_bar, text="📥 Export JSON Audit Log", command=self._export_json).pack(side="right", padx=4)

    def refresh_history_list(self) -> None:
        """Fetch all batches from database and populate treeview."""
        for item in self.tree_history.get_children():
            self.tree_history.delete(item)
        for item in self.tree_ops.get_children():
            self.tree_ops.delete(item)

        self.btn_undo.config(state="disabled")

        batches = self.engine.db.get_batches(limit=50)
        for b in batches:
            self.tree_history.insert(
                "",
                "end",
                iid=b["batch_id"],
                values=(
                    b["batch_id"],
                    b["created_at"][:19].replace("T", " "),
                    b["source_dir"],
                    b["total_files"],
                    b["moved_files"],
                    b["skipped_files"],
                    b["status"],
                )
            )

    def _on_history_batch_selected(self, event: Any) -> None:
        selected = self.tree_history.selection()
        if not selected:
            self.btn_undo.config(state="disabled")
            return

        batch_id = selected[0]
        for item in self.tree_ops.get_children():
            self.tree_ops.delete(item)

        ops = self.engine.db.get_batch_operations(batch_id)
        has_moved_files = any(op["status"] == "MOVED" for op in ops)

        for op in ops:
            self.tree_ops.insert(
                "",
                "end",
                values=(
                    op["source"],
                    op["destination"],
                    format_bytes(op["file_size"]),
                    op["status"],
                    op["rule_matched"] or "-",
                )
            )

        # Enable undo only if batch has moved files and is not already rolled back
        self.btn_undo.config(state="normal" if has_moved_files else "disabled")

    def _rollback_selected_batch(self) -> None:
        selected = self.tree_history.selection()
        if not selected:
            return
        batch_id = selected[0]

        if not messagebox.askyesno(
            "Confirm Rollback",
            f"Are you sure you want to rollback batch {batch_id}?\nAll moved files will be restored to their original locations.",
            parent=self
        ):
            return

        self.set_status(f"Rolling back batch {batch_id}...")
        self.progress_bar.config(mode="indeterminate")
        self.progress_bar.start(10)

        def worker() -> None:
            res = self.engine.rollback_batch(batch_id)
            self.after(0, lambda: self._on_rollback_done(res))

        threading.Thread(target=worker, daemon=True).start()

    def _on_rollback_done(self, res: Any) -> None:
        self.progress_bar.stop()
        self.progress_bar.config(mode="determinate", value=100)
        self.refresh_history_list()

        if res.failed_count == 0:
            messagebox.showinfo("Rollback Complete", f"Successfully restored {res.restored_count} files.")
            self.set_status(f"Rollback complete: {res.restored_count} files restored.")
        else:
            messagebox.showwarning(
                "Partial Rollback",
                f"Restored {res.restored_count} files, but {res.failed_count} files could not be restored."
            )
            self.set_status("Rollback completed with warnings.")

    def _export_csv(self) -> None:
        dest = filedialog.asksaveasfilename(
            title="Save CSV Audit Report",
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")]
        )
        if dest:
            count = self.engine.db.export_audit_csv(dest)
            messagebox.showinfo("Export Successful", f"Exported {count} audit records to:\n{dest}")

    def _export_json(self) -> None:
        dest = filedialog.asksaveasfilename(
            title="Save JSON Audit Report",
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json")]
        )
        if dest:
            count = self.engine.db.export_audit_json(dest)
            messagebox.showinfo("Export Successful", f"Exported {count} audit records to:\n{dest}")

    # =========================================================================
    # Asynchronous Execution Workflows
    # =========================================================================

    def set_status(self, text: str) -> None:
        self.lbl_status.config(text=text)

    def _start_scan_async(self) -> None:
        source_dir = self.var_source_path.get().strip()
        if not source_dir or not Path(source_dir).exists():
            messagebox.showerror("Invalid Folder", "Please choose a valid existing source folder.")
            return

        self.btn_scan.config(state="disabled")
        self.progress_bar.config(mode="determinate", value=0)
        self.set_status("Scanning directory...")

        def worker() -> None:
            try:
                date_mode = DateGroupingMode(self.var_date_mode.get())
                hier = HierarchyStyle(self.var_hierarchy.get())
                conflict = ConflictStrategy(self.var_conflict.get())
                dup_strat = DuplicateStrategy(self.var_duplicate.get())

                plan = self.engine.build_plan(
                    source_dir=source_dir,
                    target_dir=self.var_target_path.get().strip() or source_dir,
                    recursive=self.var_recursive.get(),
                    include_hidden=self.var_hidden.get(),
                    date_mode=date_mode,
                    hierarchy=hier,
                    conflict_strategy=conflict,
                    duplicate_strategy=dup_strat,
                    progress_callback=lambda msg, cur, tot: self.after(
                        0, lambda m=msg, c=cur, t=tot: self._on_scan_progress(m, c, t)
                    ),
                )
                self.after(0, lambda: self._on_scan_complete(plan))
            except Exception as exc:
                self.after(0, lambda: self._on_scan_error(str(exc)))

        threading.Thread(target=worker, daemon=True).start()

    def _on_scan_progress(self, msg: str, cur: int, total: int) -> None:
        self.set_status(msg)
        if total > 0:
            self.progress_bar["value"] = (cur / total) * 100

    def _on_scan_complete(self, plan: OrganizationPlan) -> None:
        self.btn_scan.config(state="normal")
        self.current_plan = plan
        self.progress_bar["value"] = 100
        self.set_status(f"Scan complete: {plan.total_files} files discovered.")

        self._apply_preview_filter()
        self._update_kpi_metrics()

        # Automatically switch to Preview tab
        self.notebook.select(self.tab_preview)

    def _on_scan_error(self, err_msg: str) -> None:
        self.btn_scan.config(state="normal")
        self.progress_bar["value"] = 0
        self.set_status("Scan failed.")
        messagebox.showerror("Scan Error", f"An error occurred while scanning:\n{err_msg}")

    def _execute_plan_async(self) -> None:
        if not self.current_plan or self.current_plan.files_to_move == 0:
            messagebox.showinfo("No Actions", "No eligible files selected to move.")
            return

        to_move = self.current_plan.files_to_move
        if not messagebox.askyesno(
            "Confirm Organization",
            f"Are you ready to organize {to_move} files?\n\nThis will safely move files into categorized folders. All changes are tracked and reversible.",
            parent=self
        ):
            return

        self.btn_execute.config(state="disabled")
        self.progress_bar["value"] = 0
        self.set_status("Organizing files...")

        def worker() -> None:
            try:
                res = self.engine.execute_plan(
                    self.current_plan,
                    progress_callback=lambda idx, tot, name: self.after(
                        0, lambda i=idx, t=tot, n=name: self._on_exec_progress(i, t, n)
                    ),
                )
                self.after(0, lambda: self._on_exec_complete(res))
            except Exception as exc:
                self.after(0, lambda: self._on_exec_error(str(exc)))

        threading.Thread(target=worker, daemon=True).start()

    def _on_exec_progress(self, current: int, total: int, fname: str) -> None:
        self.set_status(f"Moving ({current}/{total}): {fname}")
        if total > 0:
            self.progress_bar["value"] = (current / total) * 100

    def _on_exec_complete(self, res: ExecutionResult) -> None:
        self.btn_execute.config(state="normal")
        self.progress_bar["value"] = 100
        self.set_status(f"Execution complete: {res.moved_count} files organized.")

        # Update stats
        stats = self.engine.db.get_stats()
        self._lbl_total_moved.config(
            text=f"Total Files Organized: {stats['total_files_moved']} | Batches: {stats['total_batches']}"
        )

        self.refresh_history_list()

        msg = (
            f"Organization Batch Succeeded!\n\n"
            f"Batch ID: {res.batch_id}\n"
            f"Files Organized: {res.moved_count}\n"
            f"Files Skipped: {res.skipped_count}\n"
            f"Failed Moves: {res.failed_count}\n"
            f"Data Moved: {format_bytes(res.total_bytes_moved)}"
        )
        if res.failed_count > 0:
            msg += f"\n\nWarnings occurred on {res.failed_count} files. Check History for details."

        # Prompt user to open folder
        if messagebox.askyesno("Batch Finished", f"{msg}\n\nWould you like to open the organized folder now?"):
            target = self.current_plan.target_dir if self.current_plan else Path(self.var_target_path.get())
            if sys.platform == "win32":
                os.startfile(str(target))
            else:
                subprocess.run(["xdg-open", str(target)])

        # Clear plan
        self.current_plan = None
        self._apply_preview_filter()
        self.btn_execute.config(state="disabled")

    def _on_exec_error(self, err_msg: str) -> None:
        self.btn_execute.config(state="normal")
        self.progress_bar["value"] = 0
        self.set_status("Organization error.")
        messagebox.showerror("Execution Error", f"Encountered error during organization:\n{err_msg}")
