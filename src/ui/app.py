"""SortIQ — Smart File Intelligence
Modern, premium desktop application for context-aware file organization,
intelligent cryptographic deduplication, and reversible SQLite audit automation.
"""

from __future__ import annotations

import math
import os
import sys
import subprocess
import threading
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

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


class SortIQTheme:
    """SortIQ Design System: Obsidian & Deep Charcoal canvas with Electric Violet and Indigo accents."""

    FONT_FAMILY = "Segoe UI" if sys.platform == "win32" else "Helvetica"
    FONT_MONO = "Consolas" if sys.platform == "win32" else "Courier"

    # Deep Charcoal & Obsidian Surfaces
    BG_ROOT = "#101014"            # Application root window
    BG_SIDEBAR = "#15151D"         # Left navigation command sidebar
    BG_PANEL = "#161622"           # Main workspace panel background
    BG_CARD = "#1B1B26"            # Elevated cards, sections, metric boxes
    BG_CARD_HOVER = "#232332"      # Interactive card hover
    BG_INPUT = "#13131A"           # Text entries and form inputs
    BG_HEADER = "#13131B"          # Application header banner

    # Borders & Dividers
    BORDER = "#2B2B3D"             # Subtle refined border
    BORDER_SUBTLE = "#1F1F2E"      # Light separator line
    BORDER_FOCUS = "#8B5CF6"       # Electric Violet focus outline

    # Typography
    TEXT_MAIN = "#F5F3FF"          # Crisp high-contrast text
    TEXT_MUTED = "#A5A3B5"         # Secondary descriptive text
    TEXT_FAINT = "#716E82"         # Captions and technical metadata

    # Brand Accent Palette (SortIQ Purple / Violet / Indigo)
    ACCENT_PURPLE = "#8B5CF6"      # Primary Electric Purple
    ACCENT_PURPLE_HOVER = "#9D74FF"# Luminous purple hover
    ACCENT_PURPLE_GLOW = "#7C3AED" # Deep violet core
    ACCENT_VIOLET = "#A78BFA"      # Secondary soft violet
    ACCENT_INDIGO = "#6366F1"      # Supporting Indigo
    ACCENT_CYAN = "#06B6D4"        # Information telemetry
    ACCENT_SUCCESS = "#10B981"     # Emerald Green (Status / Complete)
    ACCENT_SUCCESS_HOVER = "#059669"
    ACCENT_WARNING = "#F59E0B"     # Amber Gold (Duplicate alert)
    ACCENT_DANGER = "#EF4444"      # Coral Red (Destructive / Rollback)
    ACCENT_DANGER_HOVER = "#DC2626"

    # Table & List Colors
    ROW_EVEN = "#161622"
    ROW_ODD = "#191926"
    ROW_SELECTED = "#2B2446"
    HEADER_BG = "#1F1F2E"
    HEADER_FG = "#F5F3FF"

    # Category Color Mapping for File Analytics
    CATEGORY_COLORS = {
        "Documents": "#8B5CF6",     # Electric Purple
        "Images": "#A78BFA",        # Light Violet
        "Code & Scripts": "#6366F1",# Indigo
        "Video": "#EC4899",         # Pink
        "Audio": "#F43F5E",         # Rose
        "Archives": "#06B6D4",      # Cyan
        "Spreadsheets & Data": "#10B981", # Emerald
        "Presentations": "#F59E0B", # Amber
        "Software_Installers": "#84CC16", # Lime
        "Other": "#64748B",         # Slate
    }


class SortIQPillButton(tk.Frame):
    """Refined pill-shaped button with smooth hover transition and responsive state."""

    def __init__(
        self,
        parent: tk.Widget,
        text: str = "",
        icon: str = "",
        command: Optional[Any] = None,
        variant: str = "primary",  # 'primary', 'secondary', 'success', 'danger', 'chip'
        padding: Tuple[int, int] = (16, 6),
        font_size: int = 9,
        cursor: str = "hand2",
    ) -> None:
        super().__init__(parent, bg=SortIQTheme.BG_PANEL, cursor=cursor)
        self.command = command
        self.variant = variant
        self.is_enabled = True
        self.pad_x, self.pad_y = padding
        self.font_size = font_size
        self.display_text = f"{icon}  {text}".strip() if icon else text

        self._calc_colors()

        self.lbl = tk.Label(
            self,
            text=self.display_text,
            font=(SortIQTheme.FONT_FAMILY, self.font_size, "bold"),
            bg=self.bg_color,
            fg=self.fg_color,
            padx=self.pad_x,
            pady=self.pad_y,
            cursor=cursor,
            relief="flat",
        )
        self.lbl.pack(fill="both", expand=True)

        self.lbl.bind("<Enter>", self._on_enter)
        self.lbl.bind("<Leave>", self._on_leave)
        self.lbl.bind("<Button-1>", self._on_click)
        self.bind("<Button-1>", self._on_click)

    def _calc_colors(self) -> None:
        if self.variant == "primary":
            self.bg_color = SortIQTheme.ACCENT_PURPLE
            self.bg_hover = SortIQTheme.ACCENT_PURPLE_HOVER
            self.fg_color = "#FFFFFF"
        elif self.variant == "success":
            self.bg_color = SortIQTheme.ACCENT_SUCCESS
            self.bg_hover = SortIQTheme.ACCENT_SUCCESS_HOVER
            self.fg_color = "#FFFFFF"
        elif self.variant == "danger":
            self.bg_color = SortIQTheme.ACCENT_DANGER
            self.bg_hover = SortIQTheme.ACCENT_DANGER_HOVER
            self.fg_color = "#FFFFFF"
        elif self.variant == "chip":
            self.bg_color = SortIQTheme.BG_CARD
            self.bg_hover = SortIQTheme.BG_CARD_HOVER
            self.fg_color = SortIQTheme.ACCENT_VIOLET
        else:  # secondary
            self.bg_color = SortIQTheme.BG_CARD
            self.bg_hover = SortIQTheme.BG_CARD_HOVER
            self.fg_color = SortIQTheme.TEXT_MAIN

    def _on_enter(self, event: Any) -> None:
        if self.is_enabled:
            self.lbl.config(bg=self.bg_hover)

    def _on_leave(self, event: Any) -> None:
        if self.is_enabled:
            self.lbl.config(bg=self.bg_color)

    def _on_click(self, event: Any) -> None:
        if self.is_enabled and self.command:
            self.command()

    def set_enabled(self, enabled: bool) -> None:
        self.is_enabled = enabled
        if enabled:
            self.lbl.config(bg=self.bg_color, fg=self.fg_color, cursor="hand2")
        else:
            self.lbl.config(bg=SortIQTheme.BG_CARD, fg=SortIQTheme.TEXT_FAINT, cursor="arrow")


class SortIQAnalyticsCanvas(tk.Canvas):
    """High-fidelity vector donut chart for native file distribution analytics."""

    def __init__(self, parent: tk.Widget, width: int = 240, height: int = 180) -> None:
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=SortIQTheme.BG_CARD,
            highlightthickness=0,
            bd=0,
        )
        self.data: Dict[str, int] = {}
        self.draw_chart({})

    def draw_chart(self, distribution: Dict[str, int]) -> None:
        self.delete("all")
        self.data = distribution or {
            "Documents": 38,
            "Images": 25,
            "Code & Scripts": 18,
            "Media": 12,
            "Archives": 7,
        }

        total = sum(self.data.values())
        if total <= 0:
            self.create_text(
                120, 90,
                text="No file data available\nScan directory to visualize",
                fill=SortIQTheme.TEXT_FAINT,
                font=(SortIQTheme.FONT_FAMILY, 9),
                justify="center"
            )
            return

        cx, cy = 80, 90
        r_outer = 62
        r_inner = 38

        # Draw donut slices
        start_angle = 90.0
        legend_items: List[Tuple[str, str, float]] = []

        for category, count in self.data.items():
            if count <= 0:
                continue
            extent = (count / total) * 360.0
            color = SortIQTheme.CATEGORY_COLORS.get(category, SortIQTheme.ACCENT_PURPLE)

            # Outer arc
            self.create_arc(
                cx - r_outer, cy - r_outer,
                cx + r_outer, cy + r_outer,
                start=start_angle,
                extent=extent,
                fill=color,
                outline=SortIQTheme.BG_CARD,
                width=2,
            )
            pct = (count / total) * 100.0
            legend_items.append((category, color, pct))
            start_angle += extent

        # Inner cutout circle (creating donut effect)
        self.create_oval(
            cx - r_inner, cy - r_inner,
            cx + r_inner, cy + r_inner,
            fill=SortIQTheme.BG_CARD,
            outline=SortIQTheme.BG_CARD,
        )

        # Center summary text
        self.create_text(
            cx, cy - 6,
            text=f"{total}",
            fill=SortIQTheme.TEXT_MAIN,
            font=(SortIQTheme.FONT_FAMILY, 13, "bold"),
        )
        self.create_text(
            cx, cy + 10,
            text="FILES",
            fill=SortIQTheme.TEXT_MUTED,
            font=(SortIQTheme.FONT_MONO, 7, "bold"),
        )

        # Legend column on the right
        lx = 150
        ly = 24
        for name, color, pct in legend_items[:5]:
            # Dot
            self.create_oval(lx, ly + 2, lx + 8, ly + 10, fill=color, outline="")
            # Label
            trunc_name = (name[:9] + "..") if len(name) > 11 else name
            self.create_text(
                lx + 14, ly + 6,
                text=f"{trunc_name} ({pct:.0f}%)",
                fill=SortIQTheme.TEXT_MUTED,
                font=(SortIQTheme.FONT_FAMILY, 8),
                anchor="w",
            )
            ly += 22


class RuleDialog(tk.Toplevel):
    """Refined modal dialog for creating or updating an organization rule in SortIQ."""

    def __init__(
        self,
        parent: FileOrganizerApp,
        rule: Optional[OrganizationRule] = None,
        title: str = "Rule Configuration",
    ) -> None:
        super().__init__(parent)
        self.title(f"SortIQ // {title}")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.configure(bg=SortIQTheme.BG_ROOT)
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
        f_font = SortIQTheme.FONT_FAMILY

        # Header banner
        header = tk.Frame(self, bg=SortIQTheme.BG_HEADER, padx=20, pady=16)
        header.pack(fill="x")

        tk.Label(
            header,
            text="Configure Classification Rule",
            font=(f_font, 13, "bold"),
            bg=SortIQTheme.BG_HEADER,
            fg=SortIQTheme.TEXT_MAIN,
        ).pack(anchor="w")

        tk.Label(
            header,
            text="Rules execute in priority order. All specified criteria must be satisfied.",
            font=(f_font, 9),
            bg=SortIQTheme.BG_HEADER,
            fg=SortIQTheme.TEXT_MUTED,
        ).pack(anchor="w", pady=(2, 0))

        # Form Container Card
        card = tk.Frame(
            self,
            bg=SortIQTheme.BG_CARD,
            padx=20,
            pady=16,
            highlightbackground=SortIQTheme.BORDER,
            highlightthickness=1,
        )
        card.pack(fill="both", expand=True, padx=20, pady=14)

        def make_row(lbl_text: str, row_idx: int) -> tk.Label:
            lbl = tk.Label(
                card,
                text=lbl_text,
                font=(f_font, 9, "bold"),
                bg=SortIQTheme.BG_CARD,
                fg=SortIQTheme.TEXT_MUTED,
            )
            lbl.grid(row=row_idx, column=0, sticky="w", pady=6)
            return lbl

        def make_entry(row_idx: int, width: int = 34) -> tk.Entry:
            entry = tk.Entry(
                card,
                bg=SortIQTheme.BG_INPUT,
                fg=SortIQTheme.TEXT_MAIN,
                insertbackground=SortIQTheme.ACCENT_PURPLE,
                relief="solid",
                bd=1,
                highlightbackground=SortIQTheme.BORDER,
                highlightcolor=SortIQTheme.ACCENT_PURPLE,
                highlightthickness=1,
                font=(f_font, 9),
                width=width,
            )
            entry.grid(row=row_idx, column=1, sticky="w", padx=10, pady=6)
            return entry

        # 1. Rule Name
        make_row("Rule Name: *", 0)
        self.entry_name = make_entry(0)

        # 2. Target Folder
        make_row("Target Subfolder: *", 1)
        self.entry_target = make_entry(1)

        # 3. Priority
        make_row("Priority (1 = Highest):", 2)
        self.entry_priority = make_entry(2, width=12)
        self.entry_priority.insert(0, "100")

        # 4. Pattern
        make_row("File Name Pattern:", 3)
        self.entry_pattern = make_entry(3)
        tk.Label(
            card,
            text="e.g. *invoice*, *tax*, regex:^Receipt_\\d+",
            font=(f_font, 8),
            bg=SortIQTheme.BG_CARD,
            fg=SortIQTheme.TEXT_FAINT,
        ).grid(row=4, column=1, sticky="w", padx=10)

        # 5. Extensions
        make_row("File Extensions:", 5)
        self.entry_extensions = make_entry(5)
        tk.Label(
            card,
            text="Comma separated: .pdf, .docx, .xlsx",
            font=(f_font, 8),
            bg=SortIQTheme.BG_CARD,
            fg=SortIQTheme.TEXT_FAINT,
        ).grid(row=6, column=1, sticky="w", padx=10)

        # 6. Min Size
        make_row("Min File Size (MB):", 7)
        self.entry_min_size = make_entry(7, width=14)

        # 7. Max Size
        make_row("Max File Size (MB):", 8)
        self.entry_max_size = make_entry(8, width=14)

        # 8. Enabled Toggle
        self.var_enabled = tk.BooleanVar(value=True)
        cb = tk.Checkbutton(
            card,
            text="Enable this rule immediately",
            variable=self.var_enabled,
            bg=SortIQTheme.BG_CARD,
            fg=SortIQTheme.TEXT_MAIN,
            selectcolor=SortIQTheme.BG_INPUT,
            activebackground=SortIQTheme.BG_CARD,
            activeforeground=SortIQTheme.ACCENT_PURPLE,
            font=(f_font, 9),
        )
        cb.grid(row=9, column=1, sticky="w", padx=10, pady=(10, 4))

        # Bottom Button Bar
        btn_bar = tk.Frame(self, bg=SortIQTheme.BG_ROOT, padx=20, pady=12)
        btn_bar.pack(fill="x")

        SortIQPillButton(btn_bar, text="Save Rule", icon="✓", variant="primary", command=self._on_save, padding=(18, 6)).pack(side="right", padx=6)
        SortIQPillButton(btn_bar, text="Cancel", variant="secondary", command=self.destroy, padding=(14, 6)).pack(side="right", padx=6)

    def _populate_fields(self) -> None:
        if not self.existing_rule:
            return
        r = self.existing_rule
        self.entry_name.insert(0, r.name)
        self.entry_target.insert(0, r.target_folder)
        self.entry_priority.delete(0, tk.END)
        self.entry_priority.insert(0, str(r.priority))
        self.var_enabled.set(r.enabled)

        cond = r.condition
        if cond.name_pattern:
            self.entry_pattern.insert(0, cond.name_pattern)
        if cond.extensions:
            self.entry_extensions.insert(0, ", ".join(cond.extensions))
        if cond.min_size_bytes is not None:
            self.entry_min_size.insert(0, str(round(cond.min_size_bytes / (1024 * 1024), 2)))
        if cond.max_size_bytes is not None:
            self.entry_max_size.insert(0, str(round(cond.max_size_bytes / (1024 * 1024), 2)))

    def _on_save(self) -> None:
        name = self.entry_name.get().strip()
        target = self.entry_target.get().strip()

        if not name or not target:
            messagebox.showwarning("Validation Error", "Rule Name and Target Subfolder are required.", parent=self)
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


class NotebookCompatibilityProxy:
    """Ensures 100% backward compatibility for legacy scripts calling app.notebook.select(...)."""

    def __init__(self, app: FileOrganizerApp) -> None:
        self.app = app

    def select(self, target: Any) -> None:
        if target == self.app.tab_folder or target == 0 or target == "0":
            self.app.switch_view("organize")
        elif target == self.app.tab_rules or target == 1 or target == "1":
            self.app.switch_view("rules")
        elif target == self.app.tab_preview or target == 2 or target == "2":
            self.app.switch_view("preview")
        elif target == self.app.tab_history or target == 3 or target == "3":
            self.app.switch_view("history")

    def index(self, tab_id: Any) -> int:
        return 4


class FileOrganizerApp(tk.Tk):
    """SortIQ — Smart File Intelligence Desktop Application."""

    def __init__(self, engine: Optional[OrganizerEngine] = None) -> None:
        super().__init__()
        self.title("SortIQ — Smart File Intelligence")
        self.geometry("1180x780")
        self.minsize(1020, 640)
        self.configure(bg=SortIQTheme.BG_ROOT)

        self.engine = engine or OrganizerEngine()
        self.current_plan: Optional[OrganizationPlan] = None
        self._filter_var = tk.StringVar()
        self.current_view_key = "dashboard"

        # Sidebar navigation widgets mapping
        self.nav_frames: Dict[str, tk.Frame] = {}
        self.nav_indicators: Dict[str, tk.Label] = {}
        self.nav_labels: Dict[str, tk.Label] = {}

        self._configure_ttk_styles()
        self._build_header_banner()
        self._build_main_split_layout()
        self._build_status_footer()

        # Backward compatibility proxy for external scripts
        self.notebook = NotebookCompatibilityProxy(self)

        # Set default scan path to Downloads folder
        default_dir = FileScanner.get_default_downloads_folder()
        self.var_source_path.set(str(default_dir))
        self.var_target_path.set(str(default_dir))

        self.refresh_rules_list()
        self.refresh_history_list()
        self._update_telemetry_metrics()

    def _configure_ttk_styles(self) -> None:
        """Configure ttk widgets to seamlessly match SortIQ theme."""
        self.style = ttk.Style(self)
        if "clam" in self.style.theme_names():
            self.style.theme_use("clam")

        f_font = SortIQTheme.FONT_FAMILY

        # Treeview styling
        self.style.configure(
            "Treeview",
            background=SortIQTheme.ROW_EVEN,
            foreground=SortIQTheme.TEXT_MAIN,
            fieldbackground=SortIQTheme.ROW_EVEN,
            bordercolor=SortIQTheme.BORDER,
            rowheight=30,
            font=(f_font, 9),
        )
        self.style.map(
            "Treeview",
            background=[("selected", SortIQTheme.ROW_SELECTED)],
            foreground=[("selected", "#FFFFFF")],
        )
        self.style.configure(
            "Treeview.Heading",
            background=SortIQTheme.HEADER_BG,
            foreground=SortIQTheme.HEADER_FG,
            font=(f_font, 9, "bold"),
            relief="flat",
            padding=[8, 8],
        )
        self.style.map(
            "Treeview.Heading",
            background=[("active", SortIQTheme.BG_CARD_HOVER)],
        )

        # Progressbar
        self.style.configure(
            "Horizontal.TProgressbar",
            troughcolor=SortIQTheme.BG_INPUT,
            background=SortIQTheme.ACCENT_PURPLE,
            bordercolor=SortIQTheme.BORDER,
            relief="flat",
        )

    def _build_header_banner(self) -> None:
        """Top banner featuring SortIQ brand mark, title, and live SQLite telemetry badge."""
        f_font = SortIQTheme.FONT_FAMILY

        self.header_frame = tk.Frame(
            self,
            bg=SortIQTheme.BG_HEADER,
            padx=20,
            pady=12,
            highlightbackground=SortIQTheme.BORDER,
            highlightthickness=1,
        )
        self.header_frame.pack(fill="x", padx=12, pady=(10, 6))

        # Brand Glyph & Titles
        left_box = tk.Frame(self.header_frame, bg=SortIQTheme.BG_HEADER)
        left_box.pack(side="left")

        title_row = tk.Frame(left_box, bg=SortIQTheme.BG_HEADER)
        title_row.pack(anchor="w")

        # SortIQ Logo Glyph
        tk.Label(
            title_row,
            text="⬢",
            font=(f_font, 18, "bold"),
            bg=SortIQTheme.BG_HEADER,
            fg=SortIQTheme.ACCENT_PURPLE,
        ).pack(side="left", padx=(0, 8))

        tk.Label(
            title_row,
            text="SortIQ",
            font=(f_font, 15, "bold"),
            bg=SortIQTheme.BG_HEADER,
            fg=SortIQTheme.TEXT_MAIN,
        ).pack(side="left")

        tk.Label(
            title_row,
            text="SMART FILE INTELLIGENCE",
            font=(SortIQTheme.FONT_MONO, 8, "bold"),
            bg=SortIQTheme.BG_CARD,
            fg=SortIQTheme.ACCENT_VIOLET,
            padx=8,
            pady=3,
        ).pack(side="left", padx=(10, 0))

        tk.Label(
            left_box,
            text="Context-Aware Local File Sorting • Cryptographic SHA-256 Deduplication • Reversible SQLite Engine",
            font=(f_font, 9),
            bg=SortIQTheme.BG_HEADER,
            fg=SortIQTheme.TEXT_MUTED,
        ).pack(anchor="w", pady=(3, 0))

        # Right Telemetry Status Pill
        right_box = tk.Frame(self.header_frame, bg=SortIQTheme.BG_HEADER)
        right_box.pack(side="right")

        self.telemetry_pill = tk.Frame(
            right_box,
            bg=SortIQTheme.BG_CARD,
            padx=12,
            pady=5,
            highlightbackground=SortIQTheme.BORDER,
            highlightthickness=1,
        )
        self.telemetry_pill.pack(side="left")

        self.lbl_telemetry = tk.Label(
            self.telemetry_pill,
            text="● Status: Optimal / SQLite Active",
            font=(f_font, 8, "bold"),
            bg=SortIQTheme.BG_CARD,
            fg=SortIQTheme.ACCENT_SUCCESS,
        )
        self.lbl_telemetry.pack()

    def _build_main_split_layout(self) -> None:
        """Main body with Left Navigation Sidebar and Dynamic Workspace Container."""
        self.body_container = tk.Frame(self, bg=SortIQTheme.BG_ROOT)
        self.body_container.pack(fill="both", expand=True, padx=12, pady=(0, 6))

        # =====================================================================
        # 1. Left Vertical Navigation Sidebar (~230px)
        # =====================================================================
        self.sidebar_frame = tk.Frame(
            self.body_container,
            bg=SortIQTheme.BG_SIDEBAR,
            width=230,
            highlightbackground=SortIQTheme.BORDER,
            highlightthickness=1,
            padx=10,
            pady=12,
        )
        self.sidebar_frame.pack(side="left", fill="y", padx=(0, 8))
        self.sidebar_frame.pack_propagate(False)

        tk.Label(
            self.sidebar_frame,
            text="NAVIGATION",
            font=(SortIQTheme.FONT_MONO, 8, "bold"),
            bg=SortIQTheme.BG_SIDEBAR,
            fg=SortIQTheme.TEXT_FAINT,
        ).pack(anchor="w", padx=8, pady=(4, 10))

        # Sidebar Menu Items
        nav_items = [
            ("dashboard", "📊", "Dashboard"),
            ("organize", "📁", "Organize Files"),
            ("rules", "⚙️", "Rule Engine"),
            ("preview", "🚀", "Plan & Simulation"),
            ("history", "📜", "History & Undo"),
            ("settings", "⚙️", "Settings & About"),
        ]

        for key, icon, label in nav_items:
            self._create_sidebar_nav_button(key, icon, label)

        # Sidebar Telemetry Box at the bottom
        sidebar_bottom = tk.Frame(
            self.sidebar_frame,
            bg=SortIQTheme.BG_CARD,
            padx=10,
            pady=10,
            highlightbackground=SortIQTheme.BORDER,
            highlightthickness=1,
        )
        sidebar_bottom.pack(side="bottom", fill="x", pady=6)

        tk.Label(
            sidebar_bottom,
            text="SYSTEM METRICS",
            font=(SortIQTheme.FONT_MONO, 8, "bold"),
            bg=SortIQTheme.BG_CARD,
            fg=SortIQTheme.ACCENT_VIOLET,
        ).pack(anchor="w")

        stats = self.engine.db.get_stats()
        self._lbl_sidebar_moved = tk.Label(
            sidebar_bottom,
            text=f"Organized: {stats['total_files_moved']} files\nBatches: {stats['total_batches']}",
            font=(SortIQTheme.FONT_FAMILY, 8),
            bg=SortIQTheme.BG_CARD,
            fg=SortIQTheme.TEXT_MUTED,
            justify="left",
        )
        self._lbl_sidebar_moved.pack(anchor="w", pady=(4, 0))

        # =====================================================================
        # 2. Dynamic Workspace Container
        # =====================================================================
        self.workspace_container = tk.Frame(
            self.body_container,
            bg=SortIQTheme.BG_PANEL,
            highlightbackground=SortIQTheme.BORDER,
            highlightthickness=1,
        )
        self.workspace_container.pack(side="right", fill="both", expand=True)

        # Initialize all 6 workspace views
        self.view_dashboard = tk.Frame(self.workspace_container, bg=SortIQTheme.BG_PANEL, padx=16, pady=14)
        self.view_organize = tk.Frame(self.workspace_container, bg=SortIQTheme.BG_PANEL, padx=16, pady=14)
        self.view_rules = tk.Frame(self.workspace_container, bg=SortIQTheme.BG_PANEL, padx=16, pady=14)
        self.view_preview = tk.Frame(self.workspace_container, bg=SortIQTheme.BG_PANEL, padx=16, pady=14)
        self.view_history = tk.Frame(self.workspace_container, bg=SortIQTheme.BG_PANEL, padx=16, pady=14)
        self.view_settings = tk.Frame(self.workspace_container, bg=SortIQTheme.BG_PANEL, padx=16, pady=14)

        # Compatibility aliases mapping to existing tabs
        self.tab_folder = self.view_organize
        self.tab_rules = self.view_rules
        self.tab_preview = self.view_preview
        self.tab_history = self.view_history

        # Build UI screens
        self._init_view_dashboard()
        self._init_view_organize()
        self._init_view_rules()
        self._init_view_preview()
        self._init_view_history()
        self._init_view_settings()

        # Display default screen
        self.switch_view("dashboard")

    def _create_sidebar_nav_button(self, key: str, icon: str, text: str) -> None:
        """Create a polished sidebar item with active indicator and hover styling."""
        f_font = SortIQTheme.FONT_FAMILY

        frame = tk.Frame(self.sidebar_frame, bg=SortIQTheme.BG_SIDEBAR, cursor="hand2")
        frame.pack(fill="x", pady=2)

        indicator = tk.Label(frame, text="", bg=SortIQTheme.BG_SIDEBAR, width=1)
        indicator.pack(side="left", fill="y")

        lbl = tk.Label(
            frame,
            text=f"  {icon}  {text}",
            font=(f_font, 9, "bold"),
            bg=SortIQTheme.BG_SIDEBAR,
            fg=SortIQTheme.TEXT_MUTED,
            anchor="w",
            padx=10,
            pady=8,
            cursor="hand2",
        )
        lbl.pack(side="left", fill="both", expand=True)

        self.nav_frames[key] = frame
        self.nav_indicators[key] = indicator
        self.nav_labels[key] = lbl

        for widget in (frame, lbl, indicator):
            widget.bind("<Button-1>", lambda e, k=key: self.switch_view(k))
            widget.bind("<Enter>", lambda e, k=key: self._on_nav_hover(k, True))
            widget.bind("<Leave>", lambda e, k=key: self._on_nav_hover(k, False))

    def _on_nav_hover(self, key: str, is_hover: bool) -> None:
        if key == self.current_view_key:
            return
        bg = SortIQTheme.BG_CARD if is_hover else SortIQTheme.BG_SIDEBAR
        fg = SortIQTheme.TEXT_MAIN if is_hover else SortIQTheme.TEXT_MUTED
        self.nav_frames[key].config(bg=bg)
        self.nav_labels[key].config(bg=bg, fg=fg)
        self.nav_indicators[key].config(bg=bg)

    def switch_view(self, key: str) -> None:
        """Switch active workspace pane and update navigation indicator states."""
        views = {
            "dashboard": self.view_dashboard,
            "organize": self.view_organize,
            "rules": self.view_rules,
            "preview": self.view_preview,
            "history": self.view_history,
            "settings": self.view_settings,
        }

        # Hide current view
        for v in views.values():
            v.pack_forget()

        # Update sidebar styling
        for k in self.nav_frames:
            if k == key:
                self.nav_frames[k].config(bg=SortIQTheme.BG_CARD)
                self.nav_labels[k].config(bg=SortIQTheme.BG_CARD, fg="#FFFFFF")
                self.nav_indicators[k].config(bg=SortIQTheme.ACCENT_PURPLE)
            else:
                self.nav_frames[k].config(bg=SortIQTheme.BG_SIDEBAR)
                self.nav_labels[k].config(bg=SortIQTheme.BG_SIDEBAR, fg=SortIQTheme.TEXT_MUTED)
                self.nav_indicators[k].config(bg=SortIQTheme.BG_SIDEBAR)

        self.current_view_key = key
        target_view = views.get(key, self.view_dashboard)
        target_view.pack(fill="both", expand=True)

        if key == "dashboard":
            self._update_telemetry_metrics()
        elif key == "rules":
            self.refresh_rules_list()
        elif key == "history":
            self.refresh_history_list()

    def _build_status_footer(self) -> None:
        """Bottom status indicator and progress bar."""
        f_font = SortIQTheme.FONT_FAMILY

        self.footer = tk.Frame(
            self,
            bg=SortIQTheme.BG_HEADER,
            padx=16,
            pady=6,
            highlightbackground=SortIQTheme.BORDER,
            highlightthickness=1,
        )
        self.footer.pack(fill="x", padx=12, pady=(0, 8), side="bottom")

        self.lbl_status = tk.Label(
            self.footer,
            text="Ready.",
            font=(f_font, 9),
            bg=SortIQTheme.BG_HEADER,
            fg=SortIQTheme.TEXT_MUTED,
        )
        self.lbl_status.pack(side="left")

        self.progress_bar = ttk.Progressbar(
            self.footer,
            orient="horizontal",
            mode="determinate",
            length=220,
            style="Horizontal.TProgressbar"
        )
        self.progress_bar.pack(side="right", padx=6)

    # =========================================================================
    # VIEW 1: Dashboard (Overview, 4 KPI Cards, Quick Action, Analytics, Recent)
    # =========================================================================

    def _init_view_dashboard(self) -> None:
        f_font = SortIQTheme.FONT_FAMILY

        # Greeting & Quick Action Header
        dash_header = tk.Frame(self.view_dashboard, bg=SortIQTheme.BG_PANEL)
        dash_header.pack(fill="x", pady=(0, 14))

        tk.Label(
            dash_header,
            text="SortIQ Workspace",
            font=(f_font, 16, "bold"),
            bg=SortIQTheme.BG_PANEL,
            fg=SortIQTheme.TEXT_MAIN,
        ).pack(anchor="w")

        tk.Label(
            dash_header,
            text="Deterministic Rule Classification • Cryptographic SHA-256 Deduplication • Reversible Operations",
            font=(f_font, 9),
            bg=SortIQTheme.BG_PANEL,
            fg=SortIQTheme.TEXT_MUTED,
        ).pack(anchor="w", pady=(2, 0))

        # 4 Metric KPI Cards (Files Scanned, Files Organized, Duplicates, Space Saved)
        kpi_container = tk.Frame(self.view_dashboard, bg=SortIQTheme.BG_PANEL)
        kpi_container.pack(fill="x", pady=(0, 14))

        def make_kpi(col_idx: int, icon_str: str, title_str: str, accent_color: str) -> Dict[str, Any]:
            card = tk.Frame(
                kpi_container,
                bg=SortIQTheme.BG_CARD,
                padx=14,
                pady=12,
                highlightbackground=SortIQTheme.BORDER,
                highlightthickness=1,
            )
            card.grid(row=0, column=col_idx, sticky="nsew", padx=4)
            kpi_container.columnconfigure(col_idx, weight=1)

            top_row = tk.Frame(card, bg=SortIQTheme.BG_CARD)
            top_row.pack(fill="x")

            tk.Label(
                top_row,
                text=icon_str,
                font=(f_font, 11),
                bg=SortIQTheme.BG_CARD,
                fg=accent_color,
            ).pack(side="left")

            tk.Label(
                top_row,
                text=f"  {title_str}",
                font=(SortIQTheme.FONT_MONO, 8, "bold"),
                bg=SortIQTheme.BG_CARD,
                fg=SortIQTheme.TEXT_MUTED,
            ).pack(side="left")

            lbl_val = tk.Label(
                card,
                text="0",
                font=(SortIQTheme.FONT_MONO, 16, "bold"),
                bg=SortIQTheme.BG_CARD,
                fg=accent_color,
            )
            lbl_val.pack(anchor="w", pady=(6, 0))

            return {"frame": card, "value": lbl_val}

        self.kpi_dash_scanned = make_kpi(0, "📁", "FILES SCANNED", SortIQTheme.ACCENT_CYAN)
        self.kpi_dash_organized = make_kpi(1, "🚀", "FILES ORGANIZED", SortIQTheme.ACCENT_SUCCESS)
        self.kpi_dash_duplicates = make_kpi(2, "⚠️", "DUPLICATES FOUND", SortIQTheme.ACCENT_WARNING)
        self.kpi_dash_reclaimed = make_kpi(3, "💾", "SPACE RECLAIMED", SortIQTheme.ACCENT_PURPLE)

        # Mid Split: Quick Workflow Card (Left) & File Analytics Donut Chart (Right)
        mid_container = tk.Frame(self.view_dashboard, bg=SortIQTheme.BG_PANEL)
        mid_container.pack(fill="x", pady=(0, 14))

        # Quick Workflow Card
        quick_card = tk.Frame(
            mid_container,
            bg=SortIQTheme.BG_CARD,
            padx=16,
            pady=14,
            highlightbackground=SortIQTheme.BORDER,
            highlightthickness=1,
        )
        quick_card.pack(side="left", fill="both", expand=True, padx=(0, 6))

        tk.Label(
            quick_card,
            text="QUICK FOLDER SORTING",
            font=(SortIQTheme.FONT_MONO, 8, "bold"),
            bg=SortIQTheme.BG_CARD,
            fg=SortIQTheme.ACCENT_VIOLET,
        ).pack(anchor="w")

        tk.Label(
            quick_card,
            text="Choose a cluttered directory and generate an organization plan:",
            font=(f_font, 9),
            bg=SortIQTheme.BG_CARD,
            fg=SortIQTheme.TEXT_MUTED,
        ).pack(anchor="w", pady=(3, 10))

        # Quick preset chips
        chip_bar = tk.Frame(quick_card, bg=SortIQTheme.BG_CARD)
        chip_bar.pack(fill="x", pady=(0, 10))

        SortIQPillButton(chip_bar, text="Downloads", icon="📥", variant="chip", command=self._set_source_downloads, padding=(10, 3), font_size=8).pack(side="left", padx=2)
        SortIQPillButton(chip_bar, text="Desktop", icon="🖥️", variant="chip", command=self._set_source_desktop, padding=(10, 3), font_size=8).pack(side="left", padx=2)
        SortIQPillButton(chip_bar, text="Sample Clutter", icon="🧪", variant="chip", command=self._set_sample_clutter, padding=(10, 3), font_size=8).pack(side="left", padx=2)

        # Action Buttons
        dash_action_bar = tk.Frame(quick_card, bg=SortIQTheme.BG_CARD)
        dash_action_bar.pack(fill="x", pady=(8, 0))

        SortIQPillButton(
            dash_action_bar,
            text="Scan & Preview Plan",
            icon="🚀",
            variant="primary",
            command=self._on_scan_clicked,
            padding=(18, 7),
            font_size=10,
        ).pack(side="left", padx=4)

        SortIQPillButton(
            dash_action_bar,
            text="Configure Options",
            icon="⚙️",
            variant="secondary",
            command=lambda: self.switch_view("organize"),
            padding=(14, 7),
        ).pack(side="left", padx=4)

        # File Analytics Card (Right)
        analytics_card = tk.Frame(
            mid_container,
            bg=SortIQTheme.BG_CARD,
            padx=14,
            pady=12,
            highlightbackground=SortIQTheme.BORDER,
            highlightthickness=1,
            width=280,
        )
        analytics_card.pack(side="right", fill="y", padx=(6, 0))

        tk.Label(
            analytics_card,
            text="FILE ANALYTICS",
            font=(SortIQTheme.FONT_MONO, 8, "bold"),
            bg=SortIQTheme.BG_CARD,
            fg=SortIQTheme.ACCENT_VIOLET,
        ).pack(anchor="w")

        self.dash_analytics_canvas = SortIQAnalyticsCanvas(analytics_card, width=260, height=140)
        self.dash_analytics_canvas.pack(fill="both", expand=True, pady=(4, 0))

        # Bottom Recent Activity Timeline
        recent_card = tk.Frame(
            self.view_dashboard,
            bg=SortIQTheme.BG_CARD,
            padx=16,
            pady=12,
            highlightbackground=SortIQTheme.BORDER,
            highlightthickness=1,
        )
        recent_card.pack(fill="both", expand=True)

        recent_header = tk.Frame(recent_card, bg=SortIQTheme.BG_CARD)
        recent_header.pack(fill="x", pady=(0, 6))

        tk.Label(
            recent_header,
            text="RECENT BATCH ACTIVITY",
            font=(SortIQTheme.FONT_MONO, 8, "bold"),
            bg=SortIQTheme.BG_CARD,
            fg=SortIQTheme.ACCENT_VIOLET,
        ).pack(side="left")

        SortIQPillButton(
            recent_header,
            text="View Audit Log",
            icon="📜",
            variant="secondary",
            command=lambda: self.switch_view("history"),
            padding=(10, 3),
            font_size=8,
        ).pack(side="right")

        cols = ("Batch ID", "Source Directory", "Target Directory", "Files Moved", "Timestamp", "Status")
        self.dash_tree_recent = ttk.Treeview(recent_card, columns=cols, show="headings", height=4)
        for c in cols:
            self.dash_tree_recent.heading(c, text=c, anchor="w")
        self.dash_tree_recent.column("Batch ID", width=90, anchor="center")
        self.dash_tree_recent.column("Source Directory", width=220, anchor="w")
        self.dash_tree_recent.column("Target Directory", width=220, anchor="w")
        self.dash_tree_recent.column("Files Moved", width=100, anchor="center")
        self.dash_tree_recent.column("Timestamp", width=150, anchor="w")
        self.dash_tree_recent.column("Status", width=110, anchor="center")

        self.dash_tree_recent.pack(fill="both", expand=True)
        self._configure_tree_tags(self.dash_tree_recent)

    # =========================================================================
    # VIEW 2: Organize Files (Granular Directory & Strategy Configuration)
    # =========================================================================

    def _init_view_organize(self) -> None:
        f_font = SortIQTheme.FONT_FAMILY

        # Section Header
        tk.Label(
            self.view_organize,
            text="Organize Files — Directory & Strategy Settings",
            font=(f_font, 14, "bold"),
            bg=SortIQTheme.BG_PANEL,
            fg=SortIQTheme.TEXT_MAIN,
        ).pack(anchor="w", pady=(0, 10))

        # 1. Directory Selection Card
        dir_card = tk.Frame(
            self.view_organize,
            bg=SortIQTheme.BG_CARD,
            padx=18,
            pady=14,
            highlightbackground=SortIQTheme.BORDER,
            highlightthickness=1,
        )
        dir_card.pack(fill="x", pady=6)

        tk.Label(
            dir_card,
            text="DIRECTORY ROUTING",
            font=(SortIQTheme.FONT_MONO, 8, "bold"),
            bg=SortIQTheme.BG_CARD,
            fg=SortIQTheme.ACCENT_VIOLET,
        ).pack(anchor="w", pady=(0, 8))

        # Source
        row_src = tk.Frame(dir_card, bg=SortIQTheme.BG_CARD)
        row_src.pack(fill="x", pady=4)
        tk.Label(row_src, text="Source Folder:     ", font=(f_font, 9, "bold"), bg=SortIQTheme.BG_CARD, fg=SortIQTheme.TEXT_MUTED).pack(side="left")
        self.var_source_path = tk.StringVar()
        self.entry_source = tk.Entry(
            row_src,
            textvariable=self.var_source_path,
            bg=SortIQTheme.BG_INPUT,
            fg=SortIQTheme.TEXT_MAIN,
            insertbackground=SortIQTheme.ACCENT_PURPLE,
            relief="solid",
            bd=1,
            highlightbackground=SortIQTheme.BORDER,
            highlightcolor=SortIQTheme.ACCENT_PURPLE,
            highlightthickness=1,
            font=(f_font, 9),
        )
        self.entry_source.pack(side="left", fill="x", expand=True, padx=8)
        SortIQPillButton(row_src, text="Browse", icon="📁", variant="secondary", command=self._browse_source, padding=(12, 4)).pack(side="left", padx=2)
        SortIQPillButton(row_src, text="Downloads", variant="chip", command=self._set_source_downloads, padding=(10, 4)).pack(side="left", padx=2)

        # Target
        row_tgt = tk.Frame(dir_card, bg=SortIQTheme.BG_CARD)
        row_tgt.pack(fill="x", pady=4)
        tk.Label(row_tgt, text="Destination Folder:", font=(f_font, 9, "bold"), bg=SortIQTheme.BG_CARD, fg=SortIQTheme.TEXT_MUTED).pack(side="left")
        self.var_target_path = tk.StringVar()
        self.entry_target = tk.Entry(
            row_tgt,
            textvariable=self.var_target_path,
            bg=SortIQTheme.BG_INPUT,
            fg=SortIQTheme.TEXT_MAIN,
            insertbackground=SortIQTheme.ACCENT_PURPLE,
            relief="solid",
            bd=1,
            highlightbackground=SortIQTheme.BORDER,
            highlightcolor=SortIQTheme.ACCENT_PURPLE,
            highlightthickness=1,
            font=(f_font, 9),
        )
        self.entry_target.pack(side="left", fill="x", expand=True, padx=8)
        SortIQPillButton(row_tgt, text="Browse", icon="📁", variant="secondary", command=self._browse_target, padding=(12, 4)).pack(side="left", padx=2)
        SortIQPillButton(row_tgt, text="Same Dir", variant="chip", command=self._set_target_same, padding=(10, 4)).pack(side="left", padx=2)

        # Quick preset chip bar
        preset_bar = tk.Frame(dir_card, bg=SortIQTheme.BG_CARD)
        preset_bar.pack(fill="x", pady=(8, 0))
        tk.Label(preset_bar, text="Quick Selection Presets:", font=(f_font, 8), bg=SortIQTheme.BG_CARD, fg=SortIQTheme.TEXT_FAINT).pack(side="left", padx=(0, 6))
        SortIQPillButton(preset_bar, text="📥 Downloads", variant="chip", command=self._set_source_downloads, padding=(8, 3), font_size=8).pack(side="left", padx=2)
        SortIQPillButton(preset_bar, text="🖥️ Desktop", variant="chip", command=self._set_source_desktop, padding=(8, 3), font_size=8).pack(side="left", padx=2)
        SortIQPillButton(preset_bar, text="🧪 Sample Clutter", variant="chip", command=self._set_sample_clutter, padding=(8, 3), font_size=8).pack(side="left", padx=2)

        # 2. Strategy & Classification Cards
        strat_card = tk.Frame(
            self.view_organize,
            bg=SortIQTheme.BG_CARD,
            padx=18,
            pady=14,
            highlightbackground=SortIQTheme.BORDER,
            highlightthickness=1,
        )
        strat_card.pack(fill="x", pady=6)

        tk.Label(
            strat_card,
            text="ORGANIZATION STRATEGY & CLASSIFICATION PROTOCOLS",
            font=(SortIQTheme.FONT_MONO, 8, "bold"),
            bg=SortIQTheme.BG_CARD,
            fg=SortIQTheme.ACCENT_VIOLET,
        ).pack(anchor="w", pady=(0, 8))

        grid_frame = tk.Frame(strat_card, bg=SortIQTheme.BG_CARD)
        grid_frame.pack(fill="x")

        # Temporal Date Grouping
        tk.Label(grid_frame, text="Date Sub-folders:", font=(f_font, 9, "bold"), bg=SortIQTheme.BG_CARD, fg=SortIQTheme.TEXT_MUTED).grid(row=0, column=0, sticky="w", pady=4)
        self.var_date_mode = tk.StringVar(value=DateGroupingMode.NONE.value)
        cbo_date = ttk.Combobox(
            grid_frame,
            textvariable=self.var_date_mode,
            values=[m.value for m in DateGroupingMode],
            state="readonly",
            width=18,
        )
        cbo_date.grid(row=0, column=1, sticky="w", padx=10, pady=4)

        # Hierarchy Style
        tk.Label(grid_frame, text="Folder Layout:", font=(f_font, 9, "bold"), bg=SortIQTheme.BG_CARD, fg=SortIQTheme.TEXT_MUTED).grid(row=0, column=2, sticky="w", padx=(20, 0), pady=4)
        self.var_hierarchy = tk.StringVar(value=HierarchyStyle.CATEGORY_FIRST.value)
        cbo_hier = ttk.Combobox(
            grid_frame,
            textvariable=self.var_hierarchy,
            values=[h.value for h in HierarchyStyle],
            state="readonly",
            width=22,
        )
        cbo_hier.grid(row=0, column=3, sticky="w", padx=10, pady=4)

        # Conflict Mode
        tk.Label(grid_frame, text="Name Collisions:", font=(f_font, 9, "bold"), bg=SortIQTheme.BG_CARD, fg=SortIQTheme.TEXT_MUTED).grid(row=1, column=0, sticky="w", pady=4)
        self.var_conflict = tk.StringVar(value=ConflictStrategy.RENAME.value)
        cbo_conf = ttk.Combobox(
            grid_frame,
            textvariable=self.var_conflict,
            values=[c.value for c in ConflictStrategy],
            state="readonly",
            width=18,
        )
        cbo_conf.grid(row=1, column=1, sticky="w", padx=10, pady=4)

        # Duplicate Handling
        tk.Label(grid_frame, text="Duplicate Handling:", font=(f_font, 9, "bold"), bg=SortIQTheme.BG_CARD, fg=SortIQTheme.TEXT_MUTED).grid(row=1, column=2, sticky="w", padx=(20, 0), pady=4)
        self.var_dup_strategy = tk.StringVar(value=DuplicateStrategy.REPORT_ONLY.value)
        cbo_dup = ttk.Combobox(
            grid_frame,
            textvariable=self.var_dup_strategy,
            values=[d.value for d in DuplicateStrategy],
            state="readonly",
            width=22,
        )
        cbo_dup.grid(row=1, column=3, sticky="w", padx=10, pady=4)

        # Checkboxes for recursion & hidden files
        opts_row = tk.Frame(strat_card, bg=SortIQTheme.BG_CARD)
        opts_row.pack(fill="x", pady=(10, 0))

        self.var_recursive = tk.BooleanVar(value=True)
        tk.Checkbutton(
            opts_row,
            text="Recursive Scan (traverse subdirectories)",
            variable=self.var_recursive,
            bg=SortIQTheme.BG_CARD,
            fg=SortIQTheme.TEXT_MAIN,
            selectcolor=SortIQTheme.BG_INPUT,
            activebackground=SortIQTheme.BG_CARD,
            activeforeground=SortIQTheme.ACCENT_PURPLE,
            font=(f_font, 9),
        ).pack(side="left", padx=(0, 20))

        self.var_include_hidden = tk.BooleanVar(value=False)
        tk.Checkbutton(
            opts_row,
            text="Include Hidden / System Files",
            variable=self.var_include_hidden,
            bg=SortIQTheme.BG_CARD,
            fg=SortIQTheme.TEXT_MAIN,
            selectcolor=SortIQTheme.BG_INPUT,
            activebackground=SortIQTheme.BG_CARD,
            activeforeground=SortIQTheme.ACCENT_PURPLE,
            font=(f_font, 9),
        ).pack(side="left")

        # Bottom Action Bar
        action_bar = tk.Frame(self.view_organize, bg=SortIQTheme.BG_PANEL)
        action_bar.pack(fill="x", pady=16)

        SortIQPillButton(
            action_bar,
            text="Initiate Scan & Generate Plan",
            icon="🚀",
            variant="primary",
            command=self._on_scan_clicked,
            padding=(22, 9),
            font_size=10,
        ).pack(side="left", padx=4)

        SortIQPillButton(
            action_bar,
            text="Open Folder in Explorer",
            icon="📁",
            variant="secondary",
            command=self._open_in_explorer,
            padding=(16, 9),
        ).pack(side="left", padx=6)

    # =========================================================================
    # VIEW 3: Rule Engine Matrix
    # =========================================================================

    def _init_view_rules(self) -> None:
        f_font = SortIQTheme.FONT_FAMILY

        top_bar = tk.Frame(self.view_rules, bg=SortIQTheme.BG_PANEL)
        top_bar.pack(fill="x", pady=(0, 10))

        tk.Label(
            top_bar,
            text="SortIQ Rule Matrix Engine",
            font=(f_font, 14, "bold"),
            bg=SortIQTheme.BG_PANEL,
            fg=SortIQTheme.TEXT_MAIN,
        ).pack(side="left")

        tk.Label(
            top_bar,
            text="Custom Priority Classification Rules",
            font=(f_font, 9),
            bg=SortIQTheme.BG_PANEL,
            fg=SortIQTheme.TEXT_MUTED,
        ).pack(side="left", padx=12)

        # Rules Treeview Table
        cols = ("Priority", "Rule Name", "Target Subfolder", "Pattern", "Extensions", "Size Bounds", "Status")
        self.tree_rules = ttk.Treeview(self.view_rules, columns=cols, show="headings", height=14)

        self.tree_rules.heading("Priority", text="Priority", anchor="center")
        self.tree_rules.heading("Rule Name", text="Rule Name", anchor="w")
        self.tree_rules.heading("Target Subfolder", text="Target Subfolder", anchor="w")
        self.tree_rules.heading("Pattern", text="Name Pattern Match", anchor="w")
        self.tree_rules.heading("Extensions", text="Extensions", anchor="w")
        self.tree_rules.heading("Size Bounds", text="Size Bounds", anchor="center")
        self.tree_rules.heading("Status", text="Status", anchor="center")

        self.tree_rules.column("Priority", width=75, anchor="center")
        self.tree_rules.column("Rule Name", width=200, anchor="w")
        self.tree_rules.column("Target Subfolder", width=180, anchor="w")
        self.tree_rules.column("Pattern", width=150, anchor="w")
        self.tree_rules.column("Extensions", width=160, anchor="w")
        self.tree_rules.column("Size Bounds", width=120, anchor="center")
        self.tree_rules.column("Status", width=100, anchor="center")

        scroll_y = ttk.Scrollbar(self.view_rules, orient="vertical", command=self.tree_rules.yview)
        self.tree_rules.configure(yscrollcommand=scroll_y.set)

        self.tree_rules.pack(side="top", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y", in_=self.view_rules)

        self._configure_tree_tags(self.tree_rules)

        # Action Buttons
        btn_bar = tk.Frame(self.view_rules, bg=SortIQTheme.BG_PANEL, pady=12)
        btn_bar.pack(fill="x")

        SortIQPillButton(btn_bar, text="Add New Rule", icon="➕", variant="primary", command=self._add_rule, padding=(16, 5)).pack(side="left", padx=4)
        SortIQPillButton(btn_bar, text="Edit Selected", icon="✏️", variant="secondary", command=self._edit_rule, padding=(14, 5)).pack(side="left", padx=4)
        SortIQPillButton(btn_bar, text="Delete Selected", icon="🗑️", variant="danger", command=self._delete_rule, padding=(14, 5)).pack(side="left", padx=4)
        SortIQPillButton(btn_bar, text="Toggle Status", icon="🔄", variant="secondary", command=self._toggle_rule, padding=(14, 5)).pack(side="left", padx=4)
        SortIQPillButton(btn_bar, text="Reset Defaults", icon="↺", variant="secondary", command=self._reset_default_rules, padding=(14, 5)).pack(side="right", padx=4)

    # =========================================================================
    # VIEW 4: Plan Simulation & Execution (Preview Table & Controls)
    # =========================================================================

    def _init_view_preview(self) -> None:
        f_font = SortIQTheme.FONT_FAMILY

        # 4 Telemetry Metric Cards
        kpi_container = tk.Frame(self.view_preview, bg=SortIQTheme.BG_PANEL)
        kpi_container.pack(fill="x", pady=(0, 10))

        def make_preview_kpi(col_idx: int, icon_str: str, title_str: str, accent_color: str) -> Dict[str, Any]:
            card = tk.Frame(
                kpi_container,
                bg=SortIQTheme.BG_CARD,
                padx=14,
                pady=10,
                highlightbackground=SortIQTheme.BORDER,
                highlightthickness=1,
            )
            card.grid(row=0, column=col_idx, sticky="nsew", padx=4)
            kpi_container.columnconfigure(col_idx, weight=1)

            top_row = tk.Frame(card, bg=SortIQTheme.BG_CARD)
            top_row.pack(fill="x")

            tk.Label(top_row, text=icon_str, font=(f_font, 11), bg=SortIQTheme.BG_CARD, fg=accent_color).pack(side="left")
            tk.Label(top_row, text=f"  {title_str}", font=(SortIQTheme.FONT_MONO, 8, "bold"), bg=SortIQTheme.BG_CARD, fg=SortIQTheme.TEXT_MUTED).pack(side="left")

            lbl_val = tk.Label(card, text="0", font=(SortIQTheme.FONT_MONO, 15, "bold"), bg=SortIQTheme.BG_CARD, fg=accent_color)
            lbl_val.pack(anchor="w", pady=(4, 0))

            return {"frame": card, "value": lbl_val}

        self.kpi_prev_discovered = make_preview_kpi(0, "📁", "FILES DISCOVERED", SortIQTheme.ACCENT_CYAN)
        self.kpi_prev_scheduled = make_preview_kpi(1, "🚀", "SCHEDULED MOVES", SortIQTheme.ACCENT_SUCCESS)
        self.kpi_prev_duplicates = make_preview_kpi(2, "⚠️", "DUPLICATES DETECTED", SortIQTheme.ACCENT_WARNING)
        self.kpi_prev_wasted = make_preview_kpi(3, "💾", "WASTED DISK SPACE", SortIQTheme.ACCENT_PURPLE)

        # Quick Filter Bar
        filter_bar = tk.Frame(self.view_preview, bg=SortIQTheme.BG_PANEL)
        filter_bar.pack(fill="x", pady=(2, 8))

        tk.Label(filter_bar, text="FILTER TABLE:", font=(SortIQTheme.FONT_MONO, 8, "bold"), bg=SortIQTheme.BG_PANEL, fg=SortIQTheme.TEXT_MUTED).pack(side="left", padx=(4, 6))
        self.entry_filter = tk.Entry(
            filter_bar,
            textvariable=self._filter_var,
            bg=SortIQTheme.BG_INPUT,
            fg=SortIQTheme.TEXT_MAIN,
            insertbackground=SortIQTheme.ACCENT_PURPLE,
            relief="solid",
            bd=1,
            highlightbackground=SortIQTheme.BORDER,
            highlightcolor=SortIQTheme.ACCENT_PURPLE,
            highlightthickness=1,
            font=(f_font, 9),
            width=22,
        )
        self.entry_filter.pack(side="left", padx=4)
        self.entry_filter.bind("<KeyRelease>", lambda e: self._apply_preview_filter())

        SortIQPillButton(filter_bar, text="Clear", variant="secondary", command=lambda: [self._filter_var.set(""), self._apply_preview_filter()], padding=(10, 3)).pack(side="left", padx=3)

        # Quick Chips
        def make_filter_chip(lbl: str, term: str) -> None:
            SortIQPillButton(
                filter_bar,
                text=lbl,
                variant="chip",
                command=lambda: [self._filter_var.set(term), self._apply_preview_filter()],
                padding=(10, 3),
                font_size=8,
            ).pack(side="left", padx=2)

        make_filter_chip("Invoices", "invoice")
        make_filter_chip("Screenshots", "screenshot")
        make_filter_chip("Duplicates", "duplicate")

        SortIQPillButton(filter_bar, text="Deselect All [ ]", variant="secondary", command=lambda: self._set_all_included(False), padding=(10, 3)).pack(side="right", padx=3)
        SortIQPillButton(filter_bar, text="Select All [✓]", variant="secondary", command=lambda: self._set_all_included(True), padding=(10, 3)).pack(side="right", padx=3)

        # Preview Treeview
        cols = ("Include", "Source File", "Destination Path", "Category / Rule", "Action", "Size", "Duplicate")
        self.tree_preview = ttk.Treeview(self.view_preview, columns=cols, show="headings", height=13)

        self.tree_preview.heading("Include", text="[✓]", anchor="center")
        self.tree_preview.heading("Source File", text="Source File Name", anchor="w")
        self.tree_preview.heading("Destination Path", text="Target Destination Path", anchor="w")
        self.tree_preview.heading("Category / Rule", text="Matched Category / Rule", anchor="w")
        self.tree_preview.heading("Action", text="Action", anchor="center")
        self.tree_preview.heading("Size", text="Size", anchor="e")
        self.tree_preview.heading("Duplicate", text="Duplicate Status", anchor="center")

        self.tree_preview.column("Include", width=50, anchor="center")
        self.tree_preview.column("Source File", width=220, anchor="w")
        self.tree_preview.column("Destination Path", width=250, anchor="w")
        self.tree_preview.column("Category / Rule", width=180, anchor="w")
        self.tree_preview.column("Action", width=120, anchor="center")
        self.tree_preview.column("Size", width=90, anchor="e")
        self.tree_preview.column("Duplicate", width=120, anchor="center")

        self.tree_preview.bind("<Double-1>", self._on_preview_double_click)

        scroll_preview = ttk.Scrollbar(self.view_preview, orient="vertical", command=self.tree_preview.yview)
        self.tree_preview.configure(yscrollcommand=scroll_preview.set)

        self.tree_preview.pack(side="top", fill="both", expand=True)
        scroll_preview.pack(side="right", fill="y", in_=self.view_preview)

        self._configure_tree_tags(self.tree_preview)

        # Bottom Execution Toolbar
        exec_bar = tk.Frame(self.view_preview, bg=SortIQTheme.BG_PANEL, pady=12)
        exec_bar.pack(fill="x")

        self.btn_execute = SortIQPillButton(
            exec_bar,
            text="Execute Organization Now",
            icon="🚀",
            variant="success",
            command=self._execute_plan_async,
            padding=(22, 8),
            font_size=10,
        )
        self.btn_execute.pack(side="left", padx=4)
        self.btn_execute.set_enabled(False)

        SortIQPillButton(
            exec_bar,
            text="Toggle Selected Item [✓]",
            variant="secondary",
            command=self._toggle_selected_preview,
            padding=(14, 8),
        ).pack(side="left", padx=6)

    # =========================================================================
    # VIEW 5: History & Rollback Audit
    # =========================================================================

    def _init_view_history(self) -> None:
        f_font = SortIQTheme.FONT_FAMILY

        top_bar = tk.Frame(self.view_history, bg=SortIQTheme.BG_PANEL)
        top_bar.pack(fill="x", pady=(0, 10))

        tk.Label(
            top_bar,
            text="SortIQ Transaction Audit & Rollback Matrix",
            font=(f_font, 14, "bold"),
            bg=SortIQTheme.BG_PANEL,
            fg=SortIQTheme.TEXT_MAIN,
        ).pack(side="left")

        tk.Label(
            top_bar,
            text="All file operations are recorded in SQLite and can be rolled back safely.",
            font=(f_font, 9),
            bg=SortIQTheme.BG_PANEL,
            fg=SortIQTheme.TEXT_MUTED,
        ).pack(side="left", padx=12)

        cols = ("Batch ID", "Source Folder", "Target Folder", "Files Moved", "Timestamp", "Status")
        self.tree_history = ttk.Treeview(self.view_history, columns=cols, show="headings", height=14)

        for col in cols:
            self.tree_history.heading(col, text=col, anchor="center" if "ID" in col or "Files" in col or "Status" in col else "w")

        self.tree_history.column("Batch ID", width=90, anchor="center")
        self.tree_history.column("Source Folder", width=250, anchor="w")
        self.tree_history.column("Target Folder", width=250, anchor="w")
        self.tree_history.column("Files Moved", width=110, anchor="center")
        self.tree_history.column("Timestamp", width=180, anchor="w")
        self.tree_history.column("Status", width=130, anchor="center")

        scroll_hist = ttk.Scrollbar(self.view_history, orient="vertical", command=self.tree_history.yview)
        self.tree_history.configure(yscrollcommand=scroll_hist.set)

        self.tree_history.pack(side="top", fill="both", expand=True)
        scroll_hist.pack(side="right", fill="y", in_=self.view_history)

        self._configure_tree_tags(self.tree_history)

        # Action bar
        act_bar = tk.Frame(self.view_history, bg=SortIQTheme.BG_PANEL, pady=12)
        act_bar.pack(fill="x")

        SortIQPillButton(
            act_bar,
            text="Rollback Selected Batch (Undo Moves)",
            icon="↺",
            variant="danger",
            command=self._rollback_selected_batch,
            padding=(20, 7),
        ).pack(side="left", padx=4)

        SortIQPillButton(
            act_bar,
            text="Refresh History",
            icon="🔄",
            variant="secondary",
            command=self.refresh_history_list,
            padding=(14, 7),
        ).pack(side="left", padx=6)

        SortIQPillButton(
            act_bar,
            text="Export CSV Audit",
            icon="📥",
            variant="secondary",
            command=self._export_history_csv,
            padding=(14, 7),
        ).pack(side="right", padx=4)

    # =========================================================================
    # VIEW 6: Settings & About Information
    # =========================================================================

    def _init_view_settings(self) -> None:
        f_font = SortIQTheme.FONT_FAMILY

        tk.Label(
            self.view_settings,
            text="SortIQ — System Settings & Configuration",
            font=(f_font, 14, "bold"),
            bg=SortIQTheme.BG_PANEL,
            fg=SortIQTheme.TEXT_MAIN,
        ).pack(anchor="w", pady=(0, 14))

        # System Config Card
        cfg_card = tk.Frame(
            self.view_settings,
            bg=SortIQTheme.BG_CARD,
            padx=18,
            pady=16,
            highlightbackground=SortIQTheme.BORDER,
            highlightthickness=1,
        )
        cfg_card.pack(fill="x", pady=6)

        tk.Label(
            cfg_card,
            text="DATABASE & STORAGE CONFIGURATION",
            font=(SortIQTheme.FONT_MONO, 8, "bold"),
            bg=SortIQTheme.BG_CARD,
            fg=SortIQTheme.ACCENT_VIOLET,
        ).pack(anchor="w", pady=(0, 8))

        db_path = str(self.engine.db.db_path)
        tk.Label(
            cfg_card,
            text=f"SQLite Database: {db_path}",
            font=(f_font, 9),
            bg=SortIQTheme.BG_CARD,
            fg=SortIQTheme.TEXT_MAIN,
        ).pack(anchor="w", pady=2)

        tk.Label(
            cfg_card,
            text="Write-Ahead Logging (WAL) Mode: Enabled for zero-lock concurrency.",
            font=(f_font, 8),
            bg=SortIQTheme.BG_CARD,
            fg=SortIQTheme.TEXT_MUTED,
        ).pack(anchor="w", pady=2)

        btn_row = tk.Frame(cfg_card, bg=SortIQTheme.BG_CARD)
        btn_row.pack(anchor="w", pady=(10, 0))

        SortIQPillButton(
            btn_row,
            text="Regenerate Sample Clutter",
            icon="🧪",
            variant="secondary",
            command=self._generate_clutter_action,
            padding=(14, 5),
        ).pack(side="left", padx=(0, 8))

        # About Card
        about_card = tk.Frame(
            self.view_settings,
            bg=SortIQTheme.BG_CARD,
            padx=18,
            pady=16,
            highlightbackground=SortIQTheme.BORDER,
            highlightthickness=1,
        )
        about_card.pack(fill="x", pady=10)

        tk.Label(
            about_card,
            text="ABOUT SORTIQ",
            font=(SortIQTheme.FONT_MONO, 8, "bold"),
            bg=SortIQTheme.BG_CARD,
            fg=SortIQTheme.ACCENT_VIOLET,
        ).pack(anchor="w", pady=(0, 8))

        tk.Label(
            about_card,
            text="SortIQ — Smart File Intelligence (Version 1.0.0 Pro Suite)\n"
                 "Developed as part of the 90 Days – 90 Projects Challenge (Day 3).\n"
                 "Autonomous context-aware local file sorting with SHA-256 deduplication and SQLite audit trail.\n"
                 "100% Python Standard Library • Cross-Platform • Zero Telemetry Leaks.",
            font=(f_font, 9),
            bg=SortIQTheme.BG_CARD,
            fg=SortIQTheme.TEXT_MUTED,
            justify="left",
        ).pack(anchor="w")

    # =========================================================================
    # Tag Configuration & Treeview Helpers
    # =========================================================================

    def _configure_tree_tags(self, tree: ttk.Treeview) -> None:
        tree.tag_configure("even", background=SortIQTheme.ROW_EVEN, foreground=SortIQTheme.TEXT_MAIN)
        tree.tag_configure("odd", background=SortIQTheme.ROW_ODD, foreground=SortIQTheme.TEXT_MAIN)
        tree.tag_configure("disabled", foreground=SortIQTheme.TEXT_FAINT)
        tree.tag_configure("duplicate", foreground=SortIQTheme.ACCENT_WARNING)
        tree.tag_configure("collision", foreground=SortIQTheme.ACCENT_DANGER)
        tree.tag_configure("rule_match", foreground=SortIQTheme.ACCENT_VIOLET)
        tree.tag_configure("success", foreground=SortIQTheme.ACCENT_SUCCESS)

    # =========================================================================
    # Event Handlers & Directory Presets
    # =========================================================================

    def _browse_source(self) -> None:
        selected = filedialog.askdirectory(title="Select Source Folder to Organize")
        if selected:
            self.var_source_path.set(selected)

    def _browse_target(self) -> None:
        selected = filedialog.askdirectory(title="Select Destination Folder")
        if selected:
            self.var_target_path.set(selected)

    def _set_source_downloads(self) -> None:
        p = str(FileScanner.get_default_downloads_folder())
        self.var_source_path.set(p)
        self.var_target_path.set(p)
        self.set_status("Source set to user Downloads folder.")

    def _set_source_desktop(self) -> None:
        p = str(Path.home() / "Desktop")
        if Path(p).exists():
            self.var_source_path.set(p)
            self.var_target_path.set(p)
            self.set_status("Source set to Desktop folder.")

    def _set_target_same(self) -> None:
        self.var_target_path.set(self.var_source_path.get())

    def _set_sample_clutter(self) -> None:
        root_dir = Path(__file__).resolve().parent.parent.parent
        clutter_dir = root_dir / "data" / "sample_clutter"
        if not clutter_dir.exists():
            clutter_dir.mkdir(parents=True, exist_ok=True)
            from scripts.generate_sample_data import generate_sample_downloads_clutter
            generate_sample_downloads_clutter(clutter_dir)

        self.var_source_path.set(str(clutter_dir))
        self.var_target_path.set(str(clutter_dir))
        self.set_status("Source set to Benchmark Sample Clutter folder.")

    def _open_in_explorer(self) -> None:
        path_str = self.var_source_path.get().strip()
        if not path_str or not Path(path_str).exists():
            messagebox.showwarning("Warning", "Source folder does not exist.")
            return
        if sys.platform == "win32":
            os.startfile(path_str)
        else:
            subprocess.run(["xdg-open", path_str])

    def _generate_clutter_action(self) -> None:
        root_dir = Path(__file__).resolve().parent.parent.parent
        clutter_dir = root_dir / "data" / "sample_clutter"
        from scripts.generate_sample_data import generate_sample_downloads_clutter
        count = generate_sample_downloads_clutter(clutter_dir)
        messagebox.showinfo("Sample Clutter Ready", f"Generated {count} benchmark sample files in:\n{clutter_dir}")
        self.set_status(f"Generated {count} sample clutter files.")

    # =========================================================================
    # Scanning & Simulation Plan
    # =========================================================================

    def _on_scan_clicked(self) -> None:
        src = self.var_source_path.get().strip()
        tgt = self.var_target_path.get().strip() or src

        if not src or not Path(src).exists():
            messagebox.showerror("Error", "Please select a valid existing source directory.")
            return

        self.set_status("Scanning directory and evaluating classification rules...")
        self.progress_bar.config(mode="indeterminate")
        self.progress_bar.start(10)

        # Switch to preview view to see simulation immediately
        self.switch_view("preview")

        threading.Thread(target=self._run_scan_worker, args=(src, tgt), daemon=True).start()

    def _run_scan_worker(self, src: str, tgt: str) -> None:
        try:
            date_mode = DateGroupingMode(self.var_date_mode.get())
            hierarchy = HierarchyStyle(self.var_hierarchy.get())
            conflict = ConflictStrategy(self.var_conflict.get())
            dup_strategy = DuplicateStrategy(self.var_dup_strategy.get())
            recursive = self.var_recursive.get()
            include_hidden = self.var_include_hidden.get()

            # Reload latest rules from DB
            rules = self.engine.db.load_rules()
            if rules:
                self.engine.rules = RuleEngine(rules)

            plan = self.engine.build_plan(
                source_dir=src,
                target_dir=tgt,
                date_mode=date_mode,
                hierarchy_style=hierarchy,
                conflict_strategy=conflict,
                duplicate_strategy=dup_strategy,
                recursive=recursive,
                include_hidden=include_hidden,
            )
            self.after(0, lambda: self._on_scan_complete(plan))
        except Exception as e:
            self.after(0, lambda: self._on_scan_error(str(e)))

    def _on_scan_complete(self, plan: OrganizationPlan) -> None:
        self.progress_bar.stop()
        self.progress_bar.config(mode="determinate", value=0)
        self.current_plan = plan

        self._populate_preview_table(plan)
        self._update_telemetry_metrics()
        self.btn_execute.set_enabled(len(plan.actions) > 0)

        n_moves = sum(1 for a in plan.actions if a.action_type != ActionType.SKIP)
        msg = f"Discovered {len(plan.scanned_files)} files: {n_moves} scheduled to move, {len(plan.duplicates)} duplicates identified."
        self.set_status(msg)

    def _on_scan_error(self, err_msg: str) -> None:
        self.progress_bar.stop()
        self.progress_bar.config(mode="determinate", value=0)
        messagebox.showerror("Scan Error", f"Failed during directory scan:\n{err_msg}")
        self.set_status("Scan failed.")

    # =========================================================================
    # Plan Preview Table Population & Filter Logic
    # =========================================================================

    def _populate_preview_table(self, plan: OrganizationPlan) -> None:
        for item in self.tree_preview.get_children():
            self.tree_preview.delete(item)

        filter_text = self._filter_var.get().lower().strip()

        for idx, action in enumerate(plan.actions):
            src_name = action.source_path.name
            tgt_rel = str(action.destination_path.relative_to(action.destination_path.parents[1])) if len(action.destination_path.parts) > 2 else action.destination_path.name
            cat_name = action.rule_name or action.category

            # Search filter check
            if filter_text:
                full_searchable = f"{src_name} {tgt_rel} {cat_name} {action.action_type.value}".lower()
                if action.is_duplicate:
                    full_searchable += " duplicate"
                if filter_text not in full_searchable:
                    continue

            inc_txt = "[✓]" if action.included else "[ ]"
            dup_txt = "CLONE (SHA-256)" if action.is_duplicate else "-"
            sz_txt = format_bytes(action.size_bytes)
            act_txt = action.action_type.value.upper()

            tags = ["even" if idx % 2 == 0 else "odd"]
            if action.is_duplicate:
                tags.append("duplicate")
            if action.is_collision:
                tags.append("collision")
            if action.rule_name:
                tags.append("rule_match")

            self.tree_preview.insert(
                "",
                "end",
                iid=str(idx),
                values=(
                    inc_txt,
                    src_name,
                    tgt_rel,
                    cat_name,
                    act_txt,
                    sz_txt,
                    dup_txt,
                ),
                tags=tags,
            )

    def _apply_preview_filter(self) -> None:
        if self.current_plan:
            self._populate_preview_table(self.current_plan)

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
        self._update_telemetry_metrics()

    def _set_all_included(self, state: bool) -> None:
        if not self.current_plan:
            return
        for action in self.current_plan.actions:
            if action.action_type != ActionType.SKIP:
                action.included = state
        self._apply_preview_filter()
        self._update_telemetry_metrics()

    # =========================================================================
    # Plan Execution & Rollback
    # =========================================================================

    def _execute_plan_async(self) -> None:
        if not self.current_plan:
            return
        included_count = sum(1 for a in self.current_plan.actions if a.included and a.action_type != ActionType.SKIP)
        if included_count == 0:
            messagebox.showinfo("No Actions", "No files are selected for organization.")
            return

        confirm = messagebox.askyesno(
            "Confirm Organization Execution",
            f"Are you sure you want to execute {included_count} file operations?\n\n"
            f"• Files will be relocated according to the active simulation plan.\n"
            f"• Operations are atomic and fully reversible via the SQLite audit trail.",
        )
        if not confirm:
            return

        self.btn_execute.set_enabled(False)
        self.set_status(f"Executing organization of {included_count} files...")
        self.progress_bar.config(mode="indeterminate")
        self.progress_bar.start(10)

        threading.Thread(target=self._run_execute_worker, daemon=True).start()

    def _run_execute_worker(self) -> None:
        try:
            res = self.engine.execute_plan(self.current_plan)
            self.after(0, lambda: self._on_execute_complete(res))
        except Exception as e:
            self.after(0, lambda: self._on_execute_error(str(e)))

    def _on_execute_complete(self, result: ExecutionResult) -> None:
        self.progress_bar.stop()
        self.progress_bar.config(mode="determinate", value=0)

        self.refresh_history_list()
        self._update_telemetry_metrics()

        msg = f"Organization Complete!\n\nSuccessfully moved: {result.files_moved} files\nFailures: {result.files_failed}"
        if result.duplicates_handled > 0:
            msg += f"\nDuplicates handled: {result.duplicates_handled}"
        if result.errors:
            msg += f"\n\nFirst error encountered:\n{result.errors[0]}"

        messagebox.showinfo("Success", msg)
        self.set_status(f"Batch #{result.batch_id} completed: {result.files_moved} files organized.")

        # Re-scan folder to show clean workspace
        self._on_scan_clicked()

    def _on_execute_error(self, err_msg: str) -> None:
        self.progress_bar.stop()
        self.progress_bar.config(mode="determinate", value=0)
        self.btn_execute.set_enabled(True)
        messagebox.showerror("Execution Failure", f"An error occurred while moving files:\n{err_msg}")
        self.set_status("Organization execution failed.")

    def _rollback_selected_batch(self) -> None:
        selected = self.tree_history.selection()
        if not selected:
            messagebox.showinfo("Select Batch", "Please select a batch from the history table to roll back.")
            return
        batch_id = str(selected[0])

        batches = self.engine.db.get_batches()
        matched = next((b for b in batches if str(b["batch_id"]) == batch_id), None)
        if not matched:
            return

        if matched["status"].lower() == "rolled_back":
            messagebox.showwarning("Already Reversible", "This batch has already been rolled back.")
            return

        confirm = messagebox.askyesno(
            "Confirm Batch Rollback",
            f"Are you sure you want to reverse Batch {batch_id}?\n\n"
            f"• Source: {matched['source_dir']}\n"
            f"• Files to return: {matched['moved_files']}\n"
            f"All moved files will be returned to their exact original locations.",
        )
        if not confirm:
            return

        self.set_status(f"Rolling back Batch {batch_id}...")
        self.progress_bar.config(mode="indeterminate")
        self.progress_bar.start(10)

        threading.Thread(target=self._run_rollback_worker, args=(batch_id,), daemon=True).start()

    def _run_rollback_worker(self, batch_id: str) -> None:
        try:
            res = self.engine.rollback_batch(batch_id)
            self.after(0, lambda: self._on_rollback_complete(batch_id, res))
        except Exception as e:
            self.after(0, lambda: self._on_rollback_error(str(e)))

    def _on_rollback_complete(self, batch_id: int, result: ExecutionResult) -> None:
        self.progress_bar.stop()
        self.progress_bar.config(mode="determinate", value=0)
        self.refresh_history_list()
        self._update_telemetry_metrics()

        msg = f"Rollback Complete for Batch #{batch_id}!\n\nFiles successfully restored: {result.files_moved}\nFailures: {result.files_failed}"
        messagebox.showinfo("Rollback Complete", msg)
        self.set_status(f"Batch #{batch_id} successfully reversed.")

    def _on_rollback_error(self, err_msg: str) -> None:
        self.progress_bar.stop()
        self.progress_bar.config(mode="determinate", value=0)
        messagebox.showerror("Rollback Error", f"Failed to rollback batch:\n{err_msg}")
        self.set_status("Rollback failed.")

    def _export_history_csv(self) -> None:
        dest_file = filedialog.asksaveasfilename(
            title="Export Operations Audit CSV",
            defaultextension=".csv",
            filetypes=[("CSV Spreadsheet", "*.csv")],
            initialfile="sortiq_audit_history.csv",
        )
        if not dest_file:
            return
        try:
            count = self.engine.db.export_operations_to_csv(Path(dest_file))
            messagebox.showinfo("Export Successful", f"Exported {count} audit records to:\n{dest_file}")
            self.set_status(f"Exported {count} audit records to CSV.")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export CSV:\n{e}")

    # =========================================================================
    # Rule Management (Add, Edit, Delete, Toggle, Reset)
    # =========================================================================

    def refresh_rules_list(self) -> None:
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

            status_txt = "ACTIVE ✓" if rule.enabled else "DISABLED"
            tag = "even" if idx % 2 == 0 else "odd"
            if not rule.enabled:
                tag = "disabled"

            self.tree_rules.insert(
                "",
                "end",
                iid=str(rule.id),
                values=(
                    f"P-{rule.priority:02d}",
                    rule.name,
                    rule.target_folder,
                    pat,
                    exts,
                    size_txt,
                    status_txt,
                ),
                tags=(tag,),
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
    # History & Telemetry Refresh
    # =========================================================================

    def refresh_history_list(self) -> None:
        for item in self.tree_history.get_children():
            self.tree_history.delete(item)
        for item in self.dash_tree_recent.get_children():
            self.dash_tree_recent.delete(item)

        batches = self.engine.db.get_batches()
        for idx, b in enumerate(batches):
            status_txt = "ROLLED_BACK" if b["status"].lower() == "rolled_back" else "COMPLETED"
            tag = "even" if idx % 2 == 0 else "odd"
            if b["status"].lower() == "rolled_back":
                tag = "duplicate"
            elif b["status"].lower() == "completed":
                tag = "success"

            created_str = b["created_at"][:19].replace("T", " ") if "T" in b["created_at"] else b["created_at"]
            row_vals = (
                str(b["batch_id"]),
                b["source_dir"],
                b["target_dir"],
                str(b["moved_files"]),
                created_str,
                status_txt,
            )
            self.tree_history.insert("", "end", iid=str(b["batch_id"]), values=row_vals, tags=(tag,))
            if idx < 5:
                self.dash_tree_recent.insert("", "end", iid=f"dash_{b['batch_id']}", values=row_vals, tags=(tag,))

    def _update_telemetry_metrics(self) -> None:
        stats = self.engine.db.get_stats()
        organized_count = stats["total_files_moved"]
        batch_count = stats["total_batches"]

        self._lbl_sidebar_moved.config(
            text=f"Organized: {organized_count} files\nBatches: {batch_count}"
        )

        # Update KPI Cards
        if self.current_plan:
            discovered_count = len(self.current_plan.scanned_files)
            scheduled_count = sum(1 for a in self.current_plan.actions if a.included and a.action_type != ActionType.SKIP)
            dup_count = len(self.current_plan.duplicates)
            wasted_bytes = sum(d.file_metadata.size_bytes for d in self.current_plan.duplicates)
            wasted_str = format_bytes(wasted_bytes)

            self.kpi_dash_scanned["value"].config(text=str(discovered_count))
            self.kpi_dash_organized["value"].config(text=str(organized_count))
            self.kpi_dash_duplicates["value"].config(text=str(dup_count))
            self.kpi_dash_reclaimed["value"].config(text=wasted_str)

            self.kpi_prev_discovered["value"].config(text=str(discovered_count))
            self.kpi_prev_scheduled["value"].config(text=str(scheduled_count))
            self.kpi_prev_duplicates["value"].config(text=str(dup_count))
            self.kpi_prev_wasted["value"].config(text=wasted_str)

            # Update Analytics Donut Chart
            cat_counts: Dict[str, int] = {}
            for a in self.current_plan.actions:
                c = a.category or "Other"
                cat_counts[c] = cat_counts.get(c, 0) + 1
            self.dash_analytics_canvas.draw_chart(cat_counts)
        else:
            self.kpi_dash_scanned["value"].config(text="0")
            self.kpi_dash_organized["value"].config(text=str(organized_count))
            self.kpi_dash_duplicates["value"].config(text="0")
            self.kpi_dash_reclaimed["value"].config(text="0 B")

            self.kpi_prev_discovered["value"].config(text="0")
            self.kpi_prev_scheduled["value"].config(text="0")
            self.kpi_prev_duplicates["value"].config(text="0")
            self.kpi_prev_wasted["value"].config(text="0 B")

    def set_status(self, message: str) -> None:
        self.lbl_status.config(text=message)
