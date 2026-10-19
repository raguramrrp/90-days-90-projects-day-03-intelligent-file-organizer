# User Guide — Context-Aware Desktop File Organization Automation

Welcome to the **Context-Aware Desktop File Organizer**! This guide walks you through every feature of the graphical user interface and command-line automation.

---

## 1. Quick Launch

Launch the application using either method:
- **Batch Script**: Double-click `run.bat`
- **Compiled Executable**: Double-click `dist\ContextAwareFileOrganizer.exe`
- **Command Line**: `python src/main.py --gui`

---

## 2. Tab 1: Folder Selection & Configuration

### Selecting Folders
1. **Source Folder**: The cluttered folder you want to organize. Click **Browse...** or click **Downloads** to automatically load your current Windows user's Downloads directory.
2. **Destination Folder**: Where organized categories will reside. By default, clicking **Same as Source** will organize files into neat subfolders directly inside the source folder. Alternatively, you can select an external drive or separate archive directory.

### Configuring Strategies
- **Date Sub-folders**:
  - `none`: Puts files directly into category folders (e.g. `Documents/report.pdf`).
  - `year`: Groups by year (e.g. `Documents/2026/report.pdf`).
  - `year_month`: Groups by year and month (e.g. `Documents/2026-10/report.pdf`).
  - `full_date`: Groups by exact day (e.g. `Documents/2026-10-19/report.pdf`).
- **Directory Layout**:
  - `category_first`: Category folder contains date subfolders (`Images/2026-10/`).
  - `date_first`: Date folder contains category subfolders (`2026-10/Images/`).
  - `category_only`: Ignores date subfolders entirely.
- **Filename Collisions**:
  - `rename`: If `report.pdf` already exists at the destination, saves as `report (1).pdf` to prevent data loss.
  - `skip`: Leaves the colliding file in the source directory untouched.
  - `overwrite`: Replaces the file at the destination.
- **Duplicate Handling**:
  - `report_only`: Shows duplicate flags in the preview table and moves normally.
  - `quarantine`: Diverts identical duplicate copies to a dedicated `_Duplicates/` folder.
  - `skip`: Keeps duplicate copies in their original location.
- **Checkboxes**:
  - `Recursive Scan`: Enable if your messy folder contains nested subdirectories you want to flatten and organize.
  - `Include Hidden Files`: Enable if you want to organize hidden files (dotfiles).

Click **"🔍 Scan Folder & Generate Organization Preview"** to run the simulation. The application will automatically switch to Tab 3.

---

## 3. Tab 2: Custom Rule Engine

The Rule Engine allows you to create custom organization rules that override or take precedence over generic extension classification. Rules are evaluated in **Priority Order** (lowest priority number = highest precedence).

### Managing Rules
- **➕ Add Rule**: Opens the rule configuration modal dialog.
  - **Rule Name**: e.g., `Tax Invoices`
  - **Target Subfolder**: e.g., `Finances/Taxes`
  - **Priority**: e.g., `15` (1 is evaluated before 100)
  - **Name Pattern**: Supports wildcards (e.g. `*tax*`, `*W2*`) or regex (`regex:^INV_\d+`)
  - **Extensions**: Comma-separated list (e.g. `.pdf, .xlsx`)
  - **Min / Max Size**: Numerical size bounds in megabytes (e.g. Min Size `100` for files over 100MB)
  - **Enabled**: Checkbox to toggle the rule on or off.
- **✏️ Edit Selected**: Modify criteria for any selected rule.
- **🗑️ Delete Selected**: Permanently remove a rule from the database.
- **🔄 Toggle Enabled**: Temporarily enable or disable a rule without deleting it.
- **↺ Reset Defaults**: Restores built-in starter presets (Screenshots, Invoices, Receipts, Resumes, Large Files, Installers).

---

## 4. Tab 3: Plan Preview & Execution

Before making any disk modifications, Tab 3 presents a complete **Dry-Run Simulation**:

### KPI Summary Banner
- **Files Scanned**: Total count of discovered files.
- **Files to Move**: Number of files scheduled for movement.
- **Duplicates**: Number of redundant copies detected.
- **Wasted Space**: Exact disk space consumed by identical duplicates.

### Interactive Preview Table
- **Filter Box**: Type any keyword (e.g. `invoice`, `.png`, `Duplicates`) to filter the table in real time.
- **Checkbox Toggle `[✓]`**: Double-click any row or select a row and click **"Toggle Selected Item"** to include or exclude specific files from being moved.
- **Select All / Deselect All**: Bulk toggle inclusion.

### Execution
Click **"🚀 Execute Organization Now"**. A confirmation modal will appear. Upon confirmation, the files are moved in milliseconds, and you will be prompted to open the organized directory directly in Windows Explorer.

---

## 5. Tab 4: History & Rollback Audit

Every organization batch is permanently logged in the SQLite audit database for 100% peace of mind.

### Undoing / Rolling Back an Organization Batch
1. Open **Tab 4: History & Undo**.
2. Select the batch you wish to reverse from the top table.
3. The lower table will display all files that were moved during that run.
4. Click **"↩️ Undo / Rollback Selected Batch"**.
5. Confirm the action. All files are safely moved back to their exact original locations, and the batch is flagged as `ROLLED_BACK`.

### Exporting Audit Logs
- Click **"📥 Export CSV Audit Log"** to save a spreadsheet-ready `.csv` file.
- Click **"📥 Export JSON Audit Log"** to save structured `.json` data for programmatic ingestion.
