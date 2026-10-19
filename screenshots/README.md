# Application UI Screenshots & Visual Guide

This directory holds visual demonstration screenshots of the **Context-Aware Desktop File Organization Automation** system.

---

## 📷 Capturing Screenshots on Windows

When running on an interactive Windows desktop session, execute the automated screenshot script:

```bash
# Ensure virtual environment is active
.\.venv\Scripts\python scripts\capture_screenshots.py
```

This will launch the application, load the synthetic test dataset, cycle through all four workflow tabs, and automatically save high-resolution screenshots into this directory:

1. `01_folder_selection_and_options.png` — Folder selection, Downloads preset, date grouping, hierarchy layout, and conflict rules.
2. `02_rule_engine_manager.png` — Priority rule engine table, condition builder, add/edit/toggle rules.
3. `03_plan_preview_and_duplicates.png` — Dry-run simulation table with source-to-target paths, rule tags, duplicate flags, and one-click execution.
4. `04_history_and_undo_audit.png` — Complete SQLite audit history log with one-click batch rollback and CSV/JSON export.

---

## 🖥️ Screen Layout & Workflow Mockups

### Screen 1: Folder Selection & Strategy Configuration (Tab 1)
```
+--------------------------------------------------------------------------------------------------+
| 📂 Context-Aware Desktop File Organizer                       Total Files: 41 | Batches: 1       |
+--------------------------------------------------------------------------------------------------+
| [ 1. Folder & Options ]  [ 2. Rule Engine ]  [ 3. Preview & Organize ]  [ 4. History & Undo ]    |
|--------------------------------------------------------------------------------------------------|
|  Folder Locations                                                                                |
|  Source Folder:      [ D:\Downloads\Messy_Folder                                ] [Browse] [Downloads]|
|  Destination Folder: [ D:\Downloads\Messy_Folder                                ] [Browse] [Same Dir] |
|                                                                                                  |
|  Organization Strategies & Rules                                                                 |
|  Date Sub-folders:    [ None / Year / Year-Month / Full-Date ]   Layout:    [ Category / Date ]  |
|  Filename Collisions: [ Auto-Rename (1) / Skip / Overwrite   ]   Duplicates:[ Report / Quarantine] |
|  [x] Recursive Scan (traverse subfolders)     [ ] Include Hidden System Files                    |
|                                                                                                  |
|  [ 🔍 Scan Folder & Generate Organization Preview ]    [ 📁 Open in Explorer ]                   |
+--------------------------------------------------------------------------------------------------+
```

### Screen 2: Custom Rule Engine (Tab 2)
```
+--------------------------------------------------------------------------------------------------+
| Active Categorization Rules (Evaluated in Ascending Priority Order):                              |
|--------------------------------------------------------------------------------------------------|
| Priority | Rule Name                  | Target Subfolder       | Pattern       | Status          |
|----------|----------------------------|------------------------|---------------|-----------------|
|    10    | Screenshots                | Screenshots            | *screenshot*  | Active ✓        |
|    20    | Invoices & Financial Rec.  | Finances/Invoices      | *invoice*     | Active ✓        |
|    25    | Receipts                   | Finances/Receipts      | *receipt*     | Active ✓        |
|    30    | Resumes & CVs              | Career/Resumes         | *resume*      | Active ✓        |
|    40    | Large Media Files (>100MB) | Large_Files            | > 100 MB      | Active ✓        |
|    50    | Software Installers & ISOs | Software_Installers    | .exe,.msi,.iso| Active ✓        |
|                                                                                                  |
|  [ ➕ Add Rule ]   [ ✏️ Edit Selected ]   [ 🗑️ Delete ]   [ 🔄 Toggle Status ]   [ ↺ Reset ]      |
+--------------------------------------------------------------------------------------------------+
```

### Screen 3: Plan Preview & Execution (Tab 3)
```
+--------------------------------------------------------------------------------------------------+
| Files Scanned: 41  |  Files to Move: 41  |  Duplicates: 6  |  Wasted Space: 317 B                |
|--------------------------------------------------------------------------------------------------|
| Filter Preview: [ invoice                        ] [Clear]   [Select All] [Deselect All]         |
|--------------------------------------------------------------------------------------------------|
| [✓]| Source File Name         | Destination Path           | Category / Rule | Action  | Size    |
|----|--------------------------|----------------------------|-----------------|---------|---------|
| [✓]| Invoice_2026_098.pdf     | Finances\Invoices\...      | Rule: Invoices  | MOVE    | 56 B    |
| [✓]| AWS_Billing_Sept2026.pdf | Finances\Invoices\...      | Rule: Invoices  | MOVE    | 58 B    |
| [✓]| AWS_Billing (Copy).pdf   | Finances\Invoices\...      | Rule: Invoices  | MOVE    | 58 B [D]|
| [✓]| Screenshot_oct14.png     | Screenshots\...            | Rule: Screensh. | MOVE    | 42 KB   |
| [✓]| report.pdf               | Documents\2026-10\...      | Documents       | MOVE    | 120 KB  |
|                                                                                                  |
|  [ 🚀 Execute Organization Now ]    [ Toggle Selected Item [✓] ]                                 |
+--------------------------------------------------------------------------------------------------+
```

### Screen 4: History & Rollback Audit Logs (Tab 4)
```
+--------------------------------------------------------------------------------------------------+
| Organization Audit Batches & Rollback History:                                [ 🔄 Refresh Log ] |
|--------------------------------------------------------------------------------------------------|
| Batch ID                  | Timestamp           | Source Folder       | Total | Moved | Status   |
|---------------------------|---------------------|---------------------|-------|-------|----------|
| batch_20261019_210000_a4f | 2026-10-19 21:00:00 | D:\Downloads        |   41  |   41  | COMPLETED|
|                                                                                                  |
| Files in Selected Batch:                                                                         |
| Source Path                     | Destination Path                  | Size   | Status | Rule     |
|---------------------------------|-----------------------------------|--------|--------|----------|
| D:\Downloads\Invoice_098.pdf    | D:\Downloads\Finances\Invoice.pdf | 56 B   | MOVED  | Invoices |
| D:\Downloads\photo.jpg          | D:\Downloads\Images\photo.jpg     | 420 KB | MOVED  | Images   |
|                                                                                                  |
|  [ ↩️ Undo / Rollback Selected Batch ]     [ 📥 Export CSV Log ]     [ 📥 Export JSON Log ]       |
+--------------------------------------------------------------------------------------------------+
```
