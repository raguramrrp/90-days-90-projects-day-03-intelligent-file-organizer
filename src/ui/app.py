"""Modern, beautifully styled Tkinter graphical user interface for desktop file organization automation."""

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


class ColorPalette:
    """Rich visual design palettes supporting Obsidian Dark and Crisp Light themes."""

    # Dark Cyber/Obsidian Theme
    DARK = {
        "name": "dark",
        "bg_root": "#0d1117",
        "bg_panel": "#161b26",
        "bg_card": "#1e2638",
        "bg_card_hover": "#26324a",
        "bg_input": "#121722",
        "border": "#28344e",
        "border_focus": "#4f638f",
        "text_main": "#f8fafc",
        "text_muted": "#94a3b8",
        "text_faint": "#64748b",
        "accent_primary": "#6366f1",        # Electric Indigo
        "accent_primary_hover": "#4f46e5",
        "accent_cyan": "#06b6d4",           # Cyan Info
        "accent_success": "#10b981",        # Mint Green
        "accent_success_hover": "#059669",
        "accent_warning": "#f59e0b",        # Amber Gold
        "accent_warning_light": "#fbbf24",
        "accent_danger": "#ef4444",         # Coral Red
        "accent_danger_hover": "#dc2626",
        "accent_purple": "#a855f7",         # Violet
        "row_even": "#141924",
        "row_odd": "#181f2d",
        "row_selected": "#2b3956",
        "header_bg": "#1e273a",
        "header_fg": "#ffffff",
        "tag_dup_bg": "#2c2114",
        "tag_dup_fg": "#fbbf24",
        "tag_col_bg": "#2d1619",
        "tag_col_fg": "#f87171",
        "tag_rule_fg": "#38bdf8",
        "tag_success_fg": "#34d399",
    }

    # Crisp Modern Light Theme
    LIGHT = {
        "name": "light",
        "bg_root": "#f1f5f9",
        "bg_panel": "#ffffff",
        "bg_card": "#f8fafc",
        "bg_card_hover": "#e2e8f0",
        "bg_input": "#ffffff",
        "border": "#cbd5e1",
        "border_focus": "#6366f1",
        "text_main": "#0f172a",
        "text_muted": "#475569",
        "text_faint": "#94a3b8",
        "accent_primary": "#4f46e5",
        "accent_primary_hover": "#4338ca",
        "accent_cyan": "#0284c7",
        "accent_success": "#059669",
        "accent_success_hover": "#047857",
        "accent_warning": "#d97706",
        "accent_warning_light": "#b45309",
        "accent_danger": "#dc2626",
        "accent_danger_hover": "#b91c1c",
        "accent_purple": "#7c3aed",
        "row_even": "#ffffff",
        "row_odd": "#f8fafc",
        "row_selected": "#e0e7ff",
        "header_bg": "#e2e8f0",
        "header_fg": "#0f172a",
        "tag_dup_bg": "#fef3c7",
        "tag_dup_fg": "#92400e",
        "tag_col_bg": "#fee2e2",
        "tag_col_fg": "#991b1b",
        "tag_rule_fg": "#0284c7",
        "tag_success_fg": "#059669",
    }

    FONT_FAMILY = "Segoe UI" if sys.platform == "win32" else "Helvetica"


class RuleDialog(tk.Toplevel):
    """Modal dialog for creating or updating an organization rule."""

    def __init__(
        self,
        parent: FileOrganizerApp,
        rule: Optional[OrganizationRule] = None,
        title: str = "Add Organization Rule",
    ) -> None:
        super().__init__(parent)
        self.parent_app = parent
        self.theme = parent.current_theme
        self.title(title)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.configure(bg=self.theme["bg_root"])
        self.result: Optional[OrganizationRule] = None
        self.existing_rule = rule

        self._build_ui()
        self._populate_fields()
        self.geometry("540x580")
        self.center_window()

    def center_window(self) -> None:
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (540 // 2)
        y = (self.winfo_screenheight() // 2) - (580 // 2)
        self.geometry(f"+{x}+{y}")

    def _build_ui(self) -> None:
        t = self.theme
        f_font = ColorPalette.FONT_FAMILY

        # Header card
        hdr = tk.Frame(self, bg=t["bg_panel"], padx=18, pady=14, highlightbackground=t["border"], highlightthickness=1)
        hdr.pack(fill="x", padx=16, pady=(16, 10))

        tk.Label(
            hdr,
            text="⚙️ Configure Organization Rule",
            font=(f_font, 13, "bold"),
            bg=t["bg_panel"],
            fg=t["text_main"],
        ).pack(anchor="w")

        tk.Label(
            hdr,
            text="Rules are evaluated in priority order (lowest number matches first).",
            font=(f_font, 9),
            bg=t["bg_panel"],
            fg=t["text_muted"],
        ).pack(anchor="w", pady=(2, 0))

        # Main Form Container
        form = tk.Frame(self, bg=t["bg_panel"], padx=18, pady=16, highlightbackground=t["border"], highlightthickness=1)
        form.pack(fill="both", expand=True, padx=16, pady=4)

        def make_row(row_idx: int, label_text: str, hint: str = "") -> tk.Entry:
            tk.Label(
                form,
                text=label_text,
                font=(f_font, 9, "bold"),
                bg=t["bg_panel"],
                fg=t["text_main"],
                anchor="w",
            ).grid(row=row_idx * 2, column=0, sticky="w", pady=(6, 2))

            entry = tk.Entry(
                form,
                bg=t["bg_input"],
                fg=t["text_main"],
                insertbackground=t["text_main"],
                relief="solid",
                bd=1,
                highlightbackground=t["border"],
                highlightcolor=t["accent_primary"],
                highlightthickness=1,
                font=(f_font, 9),
                width=34,
            )
            entry.grid(row=row_idx * 2, column=1, sticky="w", padx=12, pady=(6, 2))

            if hint:
                tk.Label(
                    form,
                    text=hint,
                    font=(f_font, 8),
                    bg=t["bg_panel"],
                    fg=t["text_faint"],
                ).grid(row=row_idx * 2 + 1, column=1, sticky="w", padx=12, pady=(0, 4))
            return entry

        # Fields
        self.entry_name = make_row(0, "Rule Name: *", "e.g. Monthly Invoices, Screenshots, Resumes")
        self.entry_target = make_row(1, "Target Subfolder: *", "Destination folder relative to root (e.g. Finances/Invoices)")
        self.entry_priority = make_row(2, "Priority (1=High):", "Precedence order (1 is evaluated before 100)")
        self.entry_priority.insert(0, "100")

        self.entry_pattern = make_row(3, "File Name Pattern:", "Wildcards like *invoice* or regex like regex:^IMG_\\d+")
        self.entry_extensions = make_row(4, "File Extensions:", "Comma-separated list (e.g. .pdf, .xlsx, .docx)")
        self.entry_min_size = make_row(5, "Min Size (MB):", "Minimum file size threshold in megabytes")
        self.entry_max_size = make_row(6, "Max Size (MB):", "Maximum file size threshold in megabytes")

        # Enabled Checkbutton
        self.var_enabled = tk.BooleanVar(value=True)
        chk = tk.Checkbutton(
            form,
            text="Rule Active / Enabled",
            variable=self.var_enabled,
            bg=t["bg_panel"],
            fg=t["text_main"],
            selectcolor=t["bg_input"],
            activebackground=t["bg_panel"],
            activeforeground=t["text_main"],
            font=(f_font, 9, "bold"),
        )
        chk.grid(row=14, column=1, sticky="w", padx=12, pady=(8, 4))

        # Bottom Action Bar
        btn_bar = tk.Frame(self, bg=t["bg_root"], padx=16, pady=12)
        btn_bar.pack(fill="x")

        tk.Button(
            btn_bar,
            text="Cancel",
            command=self.destroy,
            bg=t["bg_card"],
            fg=t["text_main"],
            activebackground=t["bg_card_hover"],
            activeforeground=t["text_main"],
            relief="solid",
            bd=1,
            padx=14,
            pady=4,
            font=(f_font, 9),
            cursor="hand2",
        ).pack(side="right", padx=6)

        tk.Button(
            btn_bar,
            text="💾 Save Rule",
            command=self._on_save,
            bg=t["accent_primary"],
            fg="#ffffff",
            activebackground=t["accent_primary_hover"],
            activeforeground="#ffffff",
            relief="flat",
            padx=16,
            pady=4,
            font=(f_font, 9, "bold"),
            cursor="hand2",
        ).pack(side="right", padx=6)

    def _populate_fields(self) -> None:
        if not self.existing_rule:
            return
        r = self.existing_rule
        self.entry_name.delete(0, tk.END)
        self.entry_name.insert(0, r.name)

        self.entry_target.delete(0, tk.END)
        self.entry_target.insert(0, r.target_folder)

        self.entry_priority.delete(0, tk.END)
        self.entry_priority.insert(0, str(r.priority))

        self.var_enabled.set(r.enabled)

        cond = r.condition
        if cond.name_pattern:
            self.entry_pattern.delete(0, tk.END)
            self.entry_pattern.insert(0, cond.name_pattern)
        if cond.extensions:
            self.entry_extensions.delete(0, tk.END)
            self.entry_extensions.insert(0, ", ".join(cond.extensions))
        if cond.min_size_bytes is not None:
            self.entry_min_size.delete(0, tk.END)
            self.entry_min_size.insert(0, str(round(cond.min_size_bytes / (1024 * 1024), 2)))
        if cond.max_size_bytes is not None:
            self.entry_max_size.delete(0, tk.END)
            self.entry_max_size.insert(0, str(round(cond.max_size_bytes / (1024 * 1024), 2)))

    def _on_save(self) -> None:
        name = self.entry_name.get().strip()
        target = self.entry_target.get().strip()

        if not name or not target:
            messagebox.showwarning("Validation Error", "Rule Name and Target Folder are required.", parent=self)
            return

        raw_ext = self.entry_extensions.get().strip()
        extensions = None
        if raw_ext:
            extensions = [
                ext.strip() if ext.strip().startswith(".") else f".{ext.strip()}"
                for ext in raw_ext.split(",")
                if ext.strip()
            ]

        min_bytes = None
        if self.entry_min_size.get().strip():
            try:
                min_bytes = int(float(self.entry_min_size.get().strip()) * 1024 * 1024)
            except ValueError:
                messagebox.showerror("Error", "Invalid Min Size value.", parent=self)
                return

        max_bytes = None
        if self.entry_max_size.get().strip():
            try:
                max_bytes = int(float(self.entry_max_size.get().strip()) * 1024 * 1024)
            except ValueError:
                messagebox.showerror("Error", "Invalid Max Size value.", parent=self)
                return

        try:
            priority = int(self.entry_priority.get().strip())
        except ValueError:
            priority = 100

        pattern = self.entry_pattern.get().strip() or None

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
            priority=priority,
            enabled=self.var_enabled.get(),
            condition=condition,
        )
        self.destroy()


class FileOrganizerApp(tk.Tk):
    """Main desktop automation window for file organization."""

    def __init__(self, engine: Optional[OrganizerEngine] = None) -> None:
        super().__init__()
        self.title("Context-Aware Desktop File Organizer")
        self.geometry("1140x760")
        self.minsize(980, 620)

        self.engine = engine or OrganizerEngine()
        self.current_plan: Optional[OrganizationPlan] = None
        self._filter_var = tk.StringVar()
        self.current_theme = ColorPalette.DARK  # Default theme

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

    def toggle_theme(self) -> None:
        """Switch between Obsidian Dark and Crisp Light visual themes."""
        if self.current_theme["name"] == "dark":
            self.current_theme = ColorPalette.LIGHT
            self.btn_theme.config(text="🌙 Dark Theme")
        else:
            self.current_theme = ColorPalette.DARK
            self.btn_theme.config(text="☀️ Light Theme")

        self._configure_styles()
        self._update_all_widget_colors()

    def _configure_styles(self) -> None:
        """Apply theme styling rules to ttk widgets."""
        t = self.current_theme
        f_font = ColorPalette.FONT_FAMILY

        self.configure(bg=t["bg_root"])
        self.style = ttk.Style(self)

        available_themes = self.style.theme_names()
        if "clam" in available_themes:
            self.style.theme_use("clam")

        # Global configs
        self.style.configure(".", font=(f_font, 9))
        self.style.configure("TFrame", background=t["bg_root"])
        self.style.configure("Panel.TFrame", background=t["bg_panel"])
        self.style.configure("Card.TFrame", background=t["bg_card"], relief="solid", borderwidth=1)

        # Labels
        self.style.configure("TLabel", background=t["bg_root"], foreground=t["text_main"])
        self.style.configure("Panel.TLabel", background=t["bg_panel"], foreground=t["text_main"])
        self.style.configure("Card.TLabel", background=t["bg_card"], foreground=t["text_main"])
        self.style.configure("Muted.TLabel", background=t["bg_root"], foreground=t["text_muted"])
        self.style.configure("PanelMuted.TLabel", background=t["bg_panel"], foreground=t["text_muted"])

        # LabelFrames
        self.style.configure(
            "TLabelframe",
            background=t["bg_panel"],
            bordercolor=t["border"],
            darkcolor=t["border"],
            lightcolor=t["border"],
            relief="solid",
            borderwidth=1
        )
        self.style.configure(
            "TLabelframe.Label",
            background=t["bg_panel"],
            foreground=t["accent_cyan"],
            font=(f_font, 10, "bold")
        )

        # Notebook & Tabs
        self.style.configure("TNotebook", background=t["bg_root"], borderwidth=0)
        self.style.configure(
            "TNotebook.Tab",
            background=t["bg_panel"],
            foreground=t["text_muted"],
            padding=[16, 9],
            font=(f_font, 9, "bold"),
            bordercolor=t["border"],
            relief="flat"
        )
        self.style.map(
            "TNotebook.Tab",
            background=[("selected", t["accent_primary"]), ("active", t["bg_card_hover"])],
            foreground=[("selected", "#ffffff"), ("active", t["text_main"])],
        )

        # Treeview styling
        self.style.configure(
            "Treeview",
            background=t["row_even"],
            foreground=t["text_main"],
            fieldbackground=t["row_even"],
            bordercolor=t["border"],
            rowheight=28,
            font=(f_font, 9),
        )
        self.style.map(
            "Treeview",
            background=[("selected", t["row_selected"])],
            foreground=[("selected", "#ffffff")],
        )
        self.style.configure(
            "Treeview.Heading",
            background=t["header_bg"],
            foreground=t["header_fg"],
            font=(f_font, 9, "bold"),
            relief="flat",
            padding=[8, 6],
        )
        self.style.map(
            "Treeview.Heading",
            background=[("active", t["border_focus"])],
        )

        # Buttons
        self.style.configure(
            "Hero.TButton",
            background=t["accent_primary"],
            foreground="#ffffff",
            font=(f_font, 10, "bold"),
            relief="flat",
            padding=[16, 7],
        )
        self.style.map(
            "Hero.TButton",
            background=[("active", t["accent_primary_hover"]), ("disabled", t["bg_card"])],
            foreground=[("disabled", t["text_faint"])],
        )

        self.style.configure(
            "Success.TButton",
            background=t["accent_success"],
            foreground="#ffffff",
            font=(f_font, 10, "bold"),
            relief="flat",
            padding=[16, 7],
        )
        self.style.map(
            "Success.TButton",
            background=[("active", t["accent_success_hover"]), ("disabled", t["bg_card"])],
            foreground=[("disabled", t["text_faint"])],
        )

        self.style.configure(
            "Danger.TButton",
            background=t["accent_danger"],
            foreground="#ffffff",
            font=(f_font, 9, "bold"),
            relief="flat",
            padding=[12, 5],
        )
        self.style.map(
            "Danger.TButton",
            background=[("active", t["accent_danger_hover"]), ("disabled", t["bg_card"])],
            foreground=[("disabled", t["text_faint"])],
        )

        self.style.configure(
            "Secondary.TButton",
            background=t["bg_card"],
            foreground=t["text_main"],
            font=(f_font, 9),
            relief="solid",
            borderwidth=1,
            bordercolor=t["border"],
            padding=[10, 5],
        )
        self.style.map(
            "Secondary.TButton",
            background=[("active", t["bg_card_hover"])],
        )

        # Progressbar
        self.style.configure(
            "Horizontal.TProgressbar",
            troughcolor=t["bg_panel"],
            background=t["accent_cyan"],
            bordercolor=t["border"],
            relief="flat",
        )

    def _update_all_widget_colors(self) -> None:
        """Update native tkinter containers when theme changes."""
        t = self.current_theme
        self.configure(bg=t["bg_root"])
        self.header_frame.configure(bg=t["bg_panel"], highlightbackground=t["border"])
        self.header_title.configure(bg=t["bg_panel"], fg=t["text_main"])
        self.header_sub.configure(bg=t["bg_panel"], fg=t["text_muted"])
        self.header_badge.configure(bg=t["accent_primary"], fg="#ffffff")
        self.stats_pill.configure(bg=t["bg_card"], highlightbackground=t["border"])
        self._lbl_total_moved.configure(bg=t["bg_card"], fg=t["accent_cyan"])
        self.btn_theme.configure(bg=t["bg_card"], fg=t["text_main"], activebackground=t["bg_card_hover"], activeforeground=t["text_main"])
        self.status_bar.configure(bg=t["bg_panel"], highlightbackground=t["border"])
        self.lbl_status.configure(bg=t["bg_panel"], fg=t["text_muted"])
        self.lbl_status_dot.configure(bg=t["bg_panel"], fg=t["accent_success"])

        # Update KPI Cards
        for card_dict in [self.kpi_card_1, self.kpi_card_2, self.kpi_card_3, self.kpi_card_4]:
            card_dict["frame"].configure(bg=t["bg_card"], highlightbackground=t["border"])
            card_dict["icon"].configure(bg=t["bg_card"])
            card_dict["title"].configure(bg=t["bg_card"], fg=t["text_muted"])
            card_dict["value"].configure(bg=t["bg_card"])

        # Update Treeviews tag styling
        self._configure_tree_tags(self.tree_rules)
        self._configure_tree_tags(self.tree_preview)
        self._configure_tree_tags(self.tree_history)
        self._configure_tree_tags(self.tree_ops)

        self.refresh_rules_list()
        self.refresh_history_list()
        self._apply_preview_filter()

    def _configure_tree_tags(self, tree: ttk.Treeview) -> None:
        t = self.current_theme
        tree.tag_configure("odd", background=t["row_odd"])
        tree.tag_configure("even", background=t["row_even"])
        tree.tag_configure("duplicate", foreground=t["tag_dup_fg"], background=t["tag_dup_bg"])
        tree.tag_configure("collision", foreground=t["tag_col_fg"], background=t["tag_col_bg"])
        tree.tag_configure("rule_match", foreground=t["tag_rule_fg"])
        tree.tag_configure("success", foreground=t["tag_success_fg"])
        tree.tag_configure("disabled", foreground=t["text_faint"])

    # =========================================================================
    # Header & Navigation
    # =========================================================================

    def _build_header(self) -> None:
        """Top banner with branding, glowing badges, live statistics, and theme switcher."""
        t = self.current_theme
        f_font = ColorPalette.FONT_FAMILY

        self.header_frame = tk.Frame(
            self,
            bg=t["bg_panel"],
            padx=18,
            pady=12,
            highlightbackground=t["border"],
            highlightthickness=1
        )
        self.header_frame.pack(fill="x", padx=12, pady=(10, 8))

        # Title & Branding
        left_box = tk.Frame(self.header_frame, bg=t["bg_panel"])
        left_box.pack(side="left")

        title_row = tk.Frame(left_box, bg=t["bg_panel"])
        title_row.pack(anchor="w")

        self.header_title = tk.Label(
            title_row,
            text="📂 Context-Aware Desktop File Organizer",
            font=(f_font, 14, "bold"),
            bg=t["bg_panel"],
            fg=t["text_main"],
        )
        self.header_title.pack(side="left")

        self.header_badge = tk.Label(
            title_row,
            text="⚡ AUTOMATION ENGINE",
            font=(f_font, 8, "bold"),
            bg=t["accent_primary"],
            fg="#ffffff",
            padx=8,
            pady=2,
            relief="flat",
        )
        self.header_badge.pack(side="left", padx=(10, 0))

        self.header_sub = tk.Label(
            left_box,
            text="Context-Aware File Classification • Deterministic Rule Engine • Two-Tier SHA-256 Deduplication • Reversible SQLite Audit",
            font=(f_font, 9),
            bg=t["bg_panel"],
            fg=t["text_muted"],
        )
        self.header_sub.pack(anchor="w", pady=(3, 0))

        # Right Controls: Stats Capsule and Theme Toggle
        right_box = tk.Frame(self.header_frame, bg=t["bg_panel"])
        right_box.pack(side="right")

        stats = self.engine.db.get_stats()
        self.stats_pill = tk.Frame(
            right_box,
            bg=t["bg_card"],
            padx=12,
            pady=4,
            highlightbackground=t["border"],
            highlightthickness=1,
        )
        self.stats_pill.pack(side="left", padx=8)

        self._lbl_total_moved = tk.Label(
            self.stats_pill,
            text=f"📊 Total Organized: {stats['total_files_moved']} files  |  Batches: {stats['total_batches']}",
            font=(f_font, 9, "bold"),
            bg=t["bg_card"],
            fg=t["accent_cyan"],
        )
        self._lbl_total_moved.pack()

        self.btn_theme = tk.Button(
            right_box,
            text="☀️ Light Theme" if t["name"] == "dark" else "🌙 Dark Theme",
            command=self.toggle_theme,
            bg=t["bg_card"],
            fg=t["text_main"],
            activebackground=t["bg_card_hover"],
            activeforeground=t["text_main"],
            relief="solid",
            bd=1,
            padx=10,
            pady=3,
            font=(f_font, 8, "bold"),
            cursor="hand2",
        )
        self.btn_theme.pack(side="left", padx=4)

    def _build_tabs(self) -> None:
        """Initialize the 4 main workflow tabs."""
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=12, pady=(0, 6))

        # Tab 1: Folder Selection & Settings
        self.tab_folder = ttk.Frame(self.notebook, padding=14)
        self.notebook.add(self.tab_folder, text="  📁 1. Folder & Options  ")
        self._init_tab_folder()

        # Tab 2: Custom Rules Engine
        self.tab_rules = ttk.Frame(self.notebook, padding=14)
        self.notebook.add(self.tab_rules, text="  ⚙️ 2. Rule Engine  ")
        self._init_tab_rules()

        # Tab 3: Plan Preview & Execution
        self.tab_preview = ttk.Frame(self.notebook, padding=14)
        self.notebook.add(self.tab_preview, text="  👁️ 3. Preview & Organize  ")
        self._init_tab_preview()

        # Tab 4: History & Rollback Audit
        self.tab_history = ttk.Frame(self.notebook, padding=14)
        self.notebook.add(self.tab_history, text="  📜 4. History & Undo  ")
        self._init_tab_history()

    def _build_status_bar(self) -> None:
        """Bottom status indicator bar."""
        t = self.current_theme
        f_font = ColorPalette.FONT_FAMILY

        self.status_bar = tk.Frame(
            self,
            bg=t["bg_panel"],
            padx=14,
            pady=5,
            highlightbackground=t["border"],
            highlightthickness=1,
        )
        self.status_bar.pack(fill="x", side="bottom")

        self.lbl_status_dot = tk.Label(
            self.status_bar,
            text="●",
            font=(f_font, 10, "bold"),
            bg=t["bg_panel"],
            fg=t["accent_success"],
        )
        self.lbl_status_dot.pack(side="left", padx=(0, 6))

        self.lbl_status = tk.Label(
            self.status_bar,
            text="Engine Ready. Select a directory and click Scan to begin.",
            font=(f_font, 9),
            bg=t["bg_panel"],
            fg=t["text_muted"],
        )
        self.lbl_status.pack(side="left")

        self.progress_bar = ttk.Progressbar(
            self.status_bar,
            orient="horizontal",
            mode="determinate",
            length=260,
            style="Horizontal.TProgressbar"
        )
        self.progress_bar.pack(side="right", padx=6)

    # =========================================================================
    # TAB 1: Folder Selection & Configuration
    # =========================================================================

    def _init_tab_folder(self) -> None:
        t = self.current_theme
        f_font = ColorPalette.FONT_FAMILY

        # Quick Preset Chips Row
        preset_frame = ttk.Frame(self.tab_folder)
        preset_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(preset_frame, text="Quick Presets:", font=(f_font, 9, "bold")).pack(side="left", padx=(4, 8))

        def make_preset_btn(label: str, cmd: Any) -> None:
            btn = ttk.Button(preset_frame, text=label, style="Secondary.TButton", command=cmd)
            btn.pack(side="left", padx=4)

        make_preset_btn("📥 Downloads Folder", self._set_source_downloads)
        make_preset_btn("🖥️ Desktop Folder", self._set_source_desktop)
        make_preset_btn("🧪 Sample Clutter Test", self._set_source_sample_clutter)

        # Directory Selectors Card
        dir_group = ttk.LabelFrame(self.tab_folder, text="  📁 Folder Locations  ", padding=14)
        dir_group.pack(fill="x", pady=6)

        # Source Directory
        ttk.Label(dir_group, text="Source Folder (to organize): *").grid(row=0, column=0, sticky="w", pady=6)
        self.var_source_path = tk.StringVar()
        ttk.Entry(dir_group, textvariable=self.var_source_path, width=60).grid(row=0, column=1, sticky="we", padx=10, pady=6)
        ttk.Button(dir_group, text="Browse...", style="Secondary.TButton", command=self._browse_source).grid(row=0, column=2, padx=4, pady=6)

        # Target Directory
        ttk.Label(dir_group, text="Destination Folder: *").grid(row=1, column=0, sticky="w", pady=6)
        self.var_target_path = tk.StringVar()
        ttk.Entry(dir_group, textvariable=self.var_target_path, width=60).grid(row=1, column=1, sticky="we", padx=10, pady=6)
        ttk.Button(dir_group, text="Browse...", style="Secondary.TButton", command=self._browse_target).grid(row=1, column=2, padx=4, pady=6)
        ttk.Button(dir_group, text="Same as Source", style="Secondary.TButton", command=self._set_target_same).grid(row=1, column=3, padx=4, pady=6)

        dir_group.columnconfigure(1, weight=1)

        # Strategy and Behavior Options Card
        opt_group = ttk.LabelFrame(self.tab_folder, text="  ⚙️ Organization Strategies & Conflict Rules  ", padding=14)
        opt_group.pack(fill="x", pady=8)

        # Date Grouping
        ttk.Label(opt_group, text="Date Sub-folders:").grid(row=0, column=0, sticky="w", pady=8, padx=6)
        self.var_date_mode = tk.StringVar(value=DateGroupingMode.NONE.value)
        cbo_date = ttk.Combobox(
            opt_group,
            textvariable=self.var_date_mode,
            values=[m.value for m in DateGroupingMode],
            state="readonly",
            width=18
        )
        cbo_date.grid(row=0, column=1, sticky="w", pady=8, padx=6)

        # Hierarchy Style
        ttk.Label(opt_group, text="Directory Layout:").grid(row=0, column=2, sticky="w", pady=8, padx=12)
        self.var_hierarchy = tk.StringVar(value=HierarchyStyle.CATEGORY_FIRST.value)
        cbo_hier = ttk.Combobox(
            opt_group,
            textvariable=self.var_hierarchy,
            values=[h.value for h in HierarchyStyle],
            state="readonly",
            width=20
        )
        cbo_hier.grid(row=0, column=3, sticky="w", pady=8, padx=6)

        # Conflict Resolution
        ttk.Label(opt_group, text="Filename Collisions:").grid(row=1, column=0, sticky="w", pady=8, padx=6)
        self.var_conflict = tk.StringVar(value=ConflictStrategy.RENAME.value)
        cbo_conflict = ttk.Combobox(
            opt_group,
            textvariable=self.var_conflict,
            values=[c.value for c in ConflictStrategy],
            state="readonly",
            width=18
        )
        cbo_conflict.grid(row=1, column=1, sticky="w", pady=8, padx=6)

        # Duplicate Handling
        ttk.Label(opt_group, text="Duplicate Handling:").grid(row=1, column=2, sticky="w", pady=8, padx=12)
        self.var_duplicate = tk.StringVar(value=DuplicateStrategy.REPORT_ONLY.value)
        cbo_dup = ttk.Combobox(
            opt_group,
            textvariable=self.var_duplicate,
            values=[d.value for d in DuplicateStrategy],
            state="readonly",
            width=20
        )
        cbo_dup.grid(row=1, column=3, sticky="w", pady=8, padx=6)

        # Checkboxes
        check_frame = ttk.Frame(opt_group)
        check_frame.grid(row=2, column=0, columnspan=4, sticky="w", pady=(10, 4), padx=6)
        self.var_recursive = tk.BooleanVar(value=False)
        ttk.Checkbutton(check_frame, text="Recursive Scan (traverse subfolders)", variable=self.var_recursive).pack(side="left", padx=(0, 14))
        self.var_hidden = tk.BooleanVar(value=False)
        ttk.Checkbutton(check_frame, text="Include Hidden Files", variable=self.var_hidden).pack(side="left", padx=14)

        # Hero Action Bar
        action_bar = ttk.Frame(self.tab_folder, padding=4)
        action_bar.pack(fill="x", pady=12)

        self.btn_scan = ttk.Button(
            action_bar,
            text="⚡ Scan Folder & Generate Organization Preview",
            style="Hero.TButton",
            command=self._start_scan_async
        )
        self.btn_scan.pack(side="left", padx=6, ipady=3)

        ttk.Button(
            action_bar,
            text="📂 Open Source in Explorer",
            style="Secondary.TButton",
            command=self._open_source_explorer
        ).pack(side="left", padx=6, ipady=3)

        # Information Guide Box
        note_box = ttk.LabelFrame(self.tab_folder, text="  💡 Quick Guide  ", padding=14)
        note_box.pack(fill="both", expand=True, pady=6)
        workflow_text = (
            "• Step 1: Select or pick a quick preset for the cluttered directory.\n"
            "• Step 2: Choose temporal date grouping (e.g. YYYY-MM) and conflict resolution rules.\n"
            "• Step 3: Click 'Scan Folder' to simulate moves safely in memory with full duplicate detection.\n"
            "• Step 4: Inspect the generated plan in Tab 3 and execute with 100% confidence.\n"
            "• Reversible: Any batch can be rolled back in 1 click under Tab 4 (History & Undo)!"
        )
        ttk.Label(note_box, text=workflow_text, font=(f_font, 9), justify="left").pack(anchor="w")

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

    def _set_source_desktop(self) -> None:
        desktop = Path.home() / "Desktop"
        if desktop.exists():
            self.var_source_path.set(str(desktop))
            self.var_target_path.set(str(desktop))

    def _set_source_sample_clutter(self) -> None:
        sample_path = Path(__file__).resolve().parent.parent.parent / "data" / "sample_clutter"
        if sample_path.exists():
            self.var_source_path.set(str(sample_path))
            self.var_target_path.set(str(sample_path))

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
        f_font = ColorPalette.FONT_FAMILY

        desc_frame = ttk.Frame(self.tab_rules)
        desc_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(
            desc_frame,
            text="Priority Categorization Rules (Evaluated in Ascending Order):",
            font=(f_font, 10, "bold")
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

        self.tree_rules.column("Priority", width=75, anchor="center")
        self.tree_rules.column("Name", width=190, anchor="w")
        self.tree_rules.column("Target Folder", width=170, anchor="w")
        self.tree_rules.column("Pattern", width=140, anchor="w")
        self.tree_rules.column("Extensions", width=150, anchor="w")
        self.tree_rules.column("Size/Age", width=110, anchor="center")
        self.tree_rules.column("Status", width=95, anchor="center")

        scroll_y = ttk.Scrollbar(self.tab_rules, orient="vertical", command=self.tree_rules.yview)
        self.tree_rules.configure(yscrollcommand=scroll_y.set)

        self.tree_rules.pack(side="top", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y", in_=self.tab_rules)

        self._configure_tree_tags(self.tree_rules)

        # Rule Action Buttons
        btn_bar = ttk.Frame(self.tab_rules, padding=(0, 12))
        btn_bar.pack(fill="x")

        ttk.Button(btn_bar, text="➕ Add Rule", style="Hero.TButton", command=self._add_rule).pack(side="left", padx=4)
        ttk.Button(btn_bar, text="✏️ Edit Selected", style="Secondary.TButton", command=self._edit_rule).pack(side="left", padx=4)
        ttk.Button(btn_bar, text="🗑️ Delete Selected", style="Danger.TButton", command=self._delete_rule).pack(side="left", padx=4)
        ttk.Button(btn_bar, text="🔄 Toggle Enabled", style="Secondary.TButton", command=self._toggle_rule).pack(side="left", padx=4)
        ttk.Button(btn_bar, text="↺ Reset Defaults", style="Secondary.TButton", command=self._reset_default_rules).pack(side="right", padx=4)

    def refresh_rules_list(self) -> None:
        """Reload and display active rules from the database."""
        for item in self.tree_rules.get_children():
            self.tree_rules.delete(item)

        rules = self.engine.db.load_rules()
        if not rules:
            self.engine.db.initialize_default_rules_if_empty(self.engine.rules.rules)
            rules = self.engine.db.load_rules()

        self.engine.rules = RuleEngine(rules)

        for idx, rule in enumerate(rules):
            cond = rule.condition
            pat = cond.name_pattern or "-"
            exts = ", ".join(cond.extensions) if cond.extensions else "Any"
            size_txt = "-"
            if cond.min_size_bytes is not None:
                size_txt = f"> {format_bytes(cond.min_size_bytes)}"
            elif cond.max_size_bytes is not None:
                size_txt = f"< {format_bytes(cond.max_size_bytes)}"

            status_txt = "Active ✓" if rule.enabled else "Disabled"
            tag = "even" if idx % 2 == 0 else "odd"
            if not rule.enabled:
                tag = "disabled"

            self.tree_rules.insert(
                "",
                "end",
                iid=str(rule.id),
                values=(
                    f"P-{rule.priority}",
                    rule.name,
                    rule.target_folder,
                    pat,
                    exts,
                    size_txt,
                    status_txt,
                ),
                tags=(tag,)
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
        t = self.current_theme
        f_font = ColorPalette.FONT_FAMILY

        # Four Elevated KPI Metric Cards
        kpi_container = ttk.Frame(self.tab_preview)
        kpi_container.pack(fill="x", pady=(0, 10))

        def create_kpi_card(col_idx: int, icon_str: str, title_str: str, accent_color: str) -> Dict[str, Any]:
            card = tk.Frame(
                kpi_container,
                bg=t["bg_card"],
                padx=14,
                pady=10,
                highlightbackground=t["border"],
                highlightthickness=1,
            )
            card.grid(row=0, column=col_idx, sticky="nsew", padx=5)
            kpi_container.columnconfigure(col_idx, weight=1)

            top_row = tk.Frame(card, bg=t["bg_card"])
            top_row.pack(fill="x")

            lbl_icon = tk.Label(top_row, text=icon_str, font=(f_font, 12), bg=t["bg_card"])
            lbl_icon.pack(side="left")

            lbl_title = tk.Label(
                top_row,
                text=title_str,
                font=(f_font, 8, "bold"),
                bg=t["bg_card"],
                fg=t["text_muted"],
            )
            lbl_title.pack(side="left", padx=6)

            lbl_val = tk.Label(
                card,
                text="0",
                font=(f_font, 16, "bold"),
                bg=t["bg_card"],
                fg=accent_color,
            )
            lbl_val.pack(anchor="w", pady=(4, 0))

            return {"frame": card, "icon": lbl_icon, "title": lbl_title, "value": lbl_val}

        self.kpi_card_1 = create_kpi_card(0, "📁", "FILES DISCOVERED", t["accent_cyan"])
        self.kpi_card_2 = create_kpi_card(1, "🚀", "SCHEDULED MOVES", t["accent_success"])
        self.kpi_card_3 = create_kpi_card(2, "⚠️", "DUPLICATES DETECTED", t["accent_warning"])
        self.kpi_card_4 = create_kpi_card(3, "💾", "WASTED DISK SPACE", t["accent_purple"])

        # Filter Bar & Quick Chip Selectors
        filter_bar = ttk.Frame(self.tab_preview)
        filter_bar.pack(fill="x", pady=(4, 8))

        ttk.Label(filter_bar, text="Filter Table:", font=(f_font, 9, "bold")).pack(side="left", padx=(4, 6))
        entry_filter = ttk.Entry(filter_bar, textvariable=self._filter_var, width=24)
        entry_filter.pack(side="left", padx=4)
        entry_filter.bind("<KeyRelease>", lambda e: self._apply_preview_filter())

        ttk.Button(filter_bar, text="Clear", style="Secondary.TButton", command=lambda: [self._filter_var.set(""), self._apply_preview_filter()]).pack(side="left", padx=4)

        # Quick Filter Chips
        def make_chip(label: str, term: str) -> None:
            ttk.Button(
                filter_bar,
                text=label,
                style="Secondary.TButton",
                command=lambda: [self._filter_var.set(term), self._apply_preview_filter()]
            ).pack(side="left", padx=2)

        make_chip("Invoices", "invoice")
        make_chip("Screenshots", "screenshot")
        make_chip("Duplicates", "duplicate")

        ttk.Button(filter_bar, text="Select All [✓]", style="Secondary.TButton", command=lambda: self._set_all_included(True)).pack(side="right", padx=4)
        ttk.Button(filter_bar, text="Deselect All [ ]", style="Secondary.TButton", command=lambda: self._set_all_included(False)).pack(side="right", padx=4)

        # Preview Treeview
        cols = ("Include", "Source File", "Destination Path", "Category / Rule", "Action", "Size", "Duplicate")
        self.tree_preview = ttk.Treeview(self.tab_preview, columns=cols, show="headings", height=14)

        self.tree_preview.heading("Include", text="[✓]", anchor="center")
        self.tree_preview.heading("Source File", text="Source File Name", anchor="w")
        self.tree_preview.heading("Destination Path", text="Destination Path", anchor="w")
        self.tree_preview.heading("Category / Rule", text="Matched Category / Rule", anchor="w")
        self.tree_preview.heading("Action", text="Action", anchor="center")
        self.tree_preview.heading("Size", text="Size", anchor="e")
        self.tree_preview.heading("Duplicate", text="Duplicate Flag", anchor="center")

        self.tree_preview.column("Include", width=48, anchor="center")
        self.tree_preview.column("Source File", width=220, anchor="w")
        self.tree_preview.column("Destination Path", width=250, anchor="w")
        self.tree_preview.column("Category / Rule", width=180, anchor="w")
        self.tree_preview.column("Action", width=120, anchor="center")
        self.tree_preview.column("Size", width=85, anchor="e")
        self.tree_preview.column("Duplicate", width=110, anchor="center")

        self.tree_preview.bind("<Double-1>", self._on_preview_double_click)

        scroll_preview = ttk.Scrollbar(self.tab_preview, orient="vertical", command=self.tree_preview.yview)
        self.tree_preview.configure(yscrollcommand=scroll_preview.set)

        self.tree_preview.pack(side="top", fill="both", expand=True)
        scroll_preview.pack(side="right", fill="y", in_=self.tab_preview)

        self._configure_tree_tags(self.tree_preview)

        # Bottom Execution Toolbar
        exec_bar = ttk.Frame(self.tab_preview, padding=(0, 10))
        exec_bar.pack(fill="x")

        self.btn_execute = ttk.Button(
            exec_bar,
            text="🚀 Execute Organization Now",
            style="Success.TButton",
            command=self._execute_plan_async,
            state="disabled"
        )
        self.btn_execute.pack(side="left", padx=6, ipady=3)

        ttk.Button(
            exec_bar,
            text="Toggle Selected Item [✓]",
            style="Secondary.TButton",
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
        self.kpi_card_1["value"].config(text=str(p.total_files))
        self.kpi_card_2["value"].config(text=str(p.files_to_move))
        self.kpi_card_3["value"].config(text=str(p.duplicate_report.total_duplicates))
        self.kpi_card_4["value"].config(text=p.duplicate_report.readable_wasted_space)
        self.btn_execute.config(state="normal" if p.files_to_move > 0 else "disabled")

    def _apply_preview_filter(self) -> None:
        """Render rows matching search filter with custom color tags."""
        for item in self.tree_preview.get_children():
            self.tree_preview.delete(item)

        if not self.current_plan:
            return

        query = self._filter_var.get().strip().lower()

        for idx, a in enumerate(self.current_plan.actions):
            if query:
                match = (
                    query in a.source_name.lower() or
                    query in str(a.relative_dest).lower() or
                    query in a.category.lower() or
                    query in a.action_type.value.lower() or
                    (query == "duplicate" and a.is_duplicate)
                )
                if not match:
                    continue

            inc_symbol = "☑" if a.included else "☐"
            dup_symbol = "⚠️ DUPLICATE" if a.is_duplicate else "-"

            # Determine row tag
            if a.is_duplicate:
                tag = "duplicate"
            elif a.action_type == ActionType.RENAME_COLLISION:
                tag = "collision"
            elif a.matched_rule and "Rule:" in a.matched_rule:
                tag = "rule_match"
            else:
                tag = "even" if idx % 2 == 0 else "odd"

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
                ),
                tags=(tag,)
            )

    # =========================================================================
    # TAB 4: History & Rollback Audit Logs
    # =========================================================================

    def _init_tab_history(self) -> None:
        f_font = ColorPalette.FONT_FAMILY

        header_bar = ttk.Frame(self.tab_history)
        header_bar.pack(fill="x", pady=(0, 10))

        ttk.Label(
            header_bar,
            text="Organization Audit Batches & Rollback History:",
            font=(f_font, 10, "bold")
        ).pack(side="left")

        ttk.Button(header_bar, text="🔄 Refresh Log", style="Secondary.TButton", command=self.refresh_history_list).pack(side="right", padx=4)

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

        self.tree_history.column("Batch ID", width=190, anchor="w")
        self.tree_history.column("Created At", width=140, anchor="center")
        self.tree_history.column("Source Folder", width=270, anchor="w")
        self.tree_history.column("Total", width=65, anchor="center")
        self.tree_history.column("Moved", width=65, anchor="center")
        self.tree_history.column("Skipped", width=65, anchor="center")
        self.tree_history.column("Status", width=110, anchor="center")

        self.tree_history.bind("<<TreeviewSelect>>", self._on_history_batch_selected)

        self.tree_history.pack(fill="x", pady=4)
        self._configure_tree_tags(self.tree_history)

        # Sub-view: Operations inside selected batch
        ttk.Label(
            self.tab_history,
            text="Files in Selected Batch (Original Paths & Operations):",
            font=(f_font, 9, "bold")
        ).pack(anchor="w", pady=(10, 4))

        sub_cols = ("Source Path", "Destination Path", "Size", "Status", "Rule / Note")
        self.tree_ops = ttk.Treeview(self.tab_history, columns=sub_cols, show="headings", height=7)
        self.tree_ops.heading("Source Path", text="Original Source Path", anchor="w")
        self.tree_ops.heading("Destination Path", text="Destination Path", anchor="w")
        self.tree_ops.heading("Size", text="Size", anchor="e")
        self.tree_ops.heading("Status", text="Status", anchor="center")
        self.tree_ops.heading("Rule / Note", text="Rule Applied", anchor="w")

        self.tree_ops.column("Source Path", width=290, anchor="w")
        self.tree_ops.column("Destination Path", width=290, anchor="w")
        self.tree_ops.column("Size", width=85, anchor="e")
        self.tree_ops.column("Status", width=95, anchor="center")
        self.tree_ops.column("Rule / Note", width=140, anchor="w")

        self.tree_ops.pack(fill="both", expand=True, pady=4)
        self._configure_tree_tags(self.tree_ops)

        # History Toolbar
        hist_bar = ttk.Frame(self.tab_history, padding=(0, 8))
        hist_bar.pack(fill="x")

        self.btn_undo = ttk.Button(
            hist_bar,
            text="↩️ Undo / Rollback Selected Batch",
            style="Danger.TButton",
            command=self._rollback_selected_batch,
            state="disabled"
        )
        self.btn_undo.pack(side="left", padx=4)

        ttk.Button(hist_bar, text="📥 Export CSV Log", style="Secondary.TButton", command=self._export_csv).pack(side="right", padx=4)
        ttk.Button(hist_bar, text="📥 Export JSON Log", style="Secondary.TButton", command=self._export_json).pack(side="right", padx=4)

    def refresh_history_list(self) -> None:
        """Fetch all batches from database and populate treeview."""
        for item in self.tree_history.get_children():
            self.tree_history.delete(item)
        for item in self.tree_ops.get_children():
            self.tree_ops.delete(item)

        self.btn_undo.config(state="disabled")

        batches = self.engine.db.get_batches(limit=50)
        for idx, b in enumerate(batches):
            status = b["status"]
            tag = "even" if idx % 2 == 0 else "odd"
            if status == "COMPLETED":
                tag = "success"
            elif status == "ROLLED_BACK":
                tag = "duplicate"  # Amber tone

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
                ),
                tags=(tag,)
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

        for idx, op in enumerate(ops):
            tag = "even" if idx % 2 == 0 else "odd"
            if op["status"] == "MOVED":
                tag = "success"
            elif op["status"] == "ROLLED_BACK":
                tag = "duplicate"

            self.tree_ops.insert(
                "",
                "end",
                values=(
                    op["source"],
                    op["destination"],
                    format_bytes(op["file_size"]),
                    op["status"],
                    op["rule_matched"] or "-",
                ),
                tags=(tag,)
            )

        self.btn_undo.config(state="normal" if has_moved_files else "disabled")

    def _rollback_selected_batch(self) -> None:
        selected = self.tree_history.selection()
        if not selected:
            return
        batch_id = selected[0]

        if not messagebox.askyesno(
            "Confirm Rollback",
            f"Are you sure you want to rollback batch {batch_id}?\n\nAll moved files will be restored to their original locations.",
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

        # Update stats
        stats = self.engine.db.get_stats()
        self._lbl_total_moved.config(
            text=f"📊 Total Organized: {stats['total_files_moved']} files  |  Batches: {stats['total_batches']}"
        )

        if res.failed_count == 0:
            messagebox.showinfo("Rollback Complete", f"Successfully restored {res.restored_count} files to original locations.")
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

    def set_status(self, text: str, is_active: bool = False) -> None:
        t = self.current_theme
        self.lbl_status.config(text=text)
        self.lbl_status_dot.config(fg=t["accent_cyan"] if is_active else t["accent_success"])

    def _start_scan_async(self) -> None:
        source_dir = self.var_source_path.get().strip()
        if not source_dir or not Path(source_dir).exists():
            messagebox.showerror("Invalid Folder", "Please choose a valid existing source folder.")
            return

        self.btn_scan.config(state="disabled")
        self.progress_bar.config(mode="determinate", value=0)
        self.set_status("Scanning directory...", is_active=True)

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
        self.set_status(msg, is_active=True)
        if total > 0:
            self.progress_bar["value"] = (cur / total) * 100

    def _on_scan_complete(self, plan: OrganizationPlan) -> None:
        self.btn_scan.config(state="normal")
        self.current_plan = plan
        self.progress_bar["value"] = 100
        self.set_status(f"Scan complete: {plan.total_files} files discovered.")

        self._apply_preview_filter()
        self._update_kpi_metrics()
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
            f"Are you ready to organize {to_move} files?\n\nThis will safely move files into categorized folders. All changes are recorded and reversible.",
            parent=self
        ):
            return

        self.btn_execute.config(state="disabled")
        self.progress_bar["value"] = 0
        self.set_status("Organizing files...", is_active=True)

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
        self.set_status(f"Moving ({current}/{total}): {fname}", is_active=True)
        if total > 0:
            self.progress_bar["value"] = (current / total) * 100

    def _on_exec_complete(self, res: ExecutionResult) -> None:
        self.btn_execute.config(state="normal")
        self.progress_bar["value"] = 100
        self.set_status(f"Execution complete: {res.moved_count} files organized.")

        # Update stats
        stats = self.engine.db.get_stats()
        self._lbl_total_moved.config(
            text=f"📊 Total Organized: {stats['total_files_moved']} files  |  Batches: {stats['total_batches']}"
        )

        self.refresh_history_list()

        msg = (
            f"Organization Batch Succeeded!\n\n"
            f"Batch ID: {res.batch_id}\n"
            f"Files Organized: {res.moved_count}\n"
            f"Files Skipped: {res.skipped_count}\n"
            f"Failed Moves: {res.failed_count}\n"
            f"Data Transferred: {format_bytes(res.total_bytes_moved)}"
        )
        if res.failed_count > 0:
            msg += f"\n\nWarnings occurred on {res.failed_count} files. Check History for details."

        if messagebox.askyesno("Batch Finished", f"{msg}\n\nWould you like to open the organized folder now?"):
            target = self.current_plan.target_dir if self.current_plan else Path(self.var_target_path.get())
            if sys.platform == "win32":
                os.startfile(str(target))
            else:
                subprocess.run(["xdg-open", str(target)])

        self.current_plan = None
        self._apply_preview_filter()
        self.btn_execute.config(state="disabled")

    def _on_exec_error(self, err_msg: str) -> None:
        self.btn_execute.config(state="normal")
        self.progress_bar["value"] = 0
        self.set_status("Organization error.")
        messagebox.showerror("Execution Error", f"Encountered error during organization:\n{err_msg}")
