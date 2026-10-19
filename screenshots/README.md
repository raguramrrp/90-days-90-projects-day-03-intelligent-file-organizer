# SortIQ — Smart File Intelligence
## UI Screenshots & Visual Guide

This directory holds visual demonstration assets and layout documentation for **SortIQ — Smart File Intelligence** (Context-Aware Desktop File Organization Automation system).

---

## 🎨 Design Concept Rendering

![SortIQ Desktop UI Concept](sortiq_design_concept.jpg)

The redesigned interface features:
- **Obsidian Dark Canvas (`#101014`)** with elevated card surfaces (`#1B1B26`) and electric violet accents (`#8B5CF6`).
- **Vertical Command Sidebar** navigating between Dashboard, Organize Files, Rule Engine, Plan Simulation, History & Undo, and Settings.
- **4 Telemetry Metric Cards** (Files Scanned, Files Organized, Duplicates Found, Space Reclaimed).
- **Native Vector Donut Chart** displaying category distributions dynamically calculated from scanned files.
- **Transaction Audit Matrix** supporting one-click rollback of any historical batch.

---

## 🖥️ Screen Layout & Workflow Mockup

### Main Dashboard & Workspace
```
+----------------------------------------------------------------------------------------------------------+
| ⬢ SortIQ  [SMART FILE INTELLIGENCE]                        ● Status: Optimal / SQLite Active             |
+----------------------------------------------------------------------------------------------------------+
|  [SIDEBAR]            |  [DASHBOARD WORKSPACE]                                                           |
|  NAVIGATION           |  SortIQ Workspace                                                                |
|  ▌ 📊 Dashboard       |  Context-Aware Local File Sorting • Cryptographic SHA-256 Deduplication           |
|    📁 Organize Files  |                                                                                  |
|    ⚙️ Rule Engine      |  [ 📁 SCANNED: 41 ]  [ 🚀 ORGANIZED: 41 ]  [ ⚠️ DUPLICATES: 6 ]  [ 💾 RECLAIMED: 317 B ]|
|    🚀 Plan Simulation |                                                                                  |
|    📜 History & Undo  |  QUICK FOLDER SORTING                     |  FILE ANALYTICS                      |
|    ⚙️ Settings         |  Source: [ D:\Downloads\Sample_Clutter ]  |  [ Donut Chart: Documents 38%        |
|                       |  Presets: [Downloads] [Desktop] [Clutter] |                 Images 25%, Code 18% |
|  SYSTEM METRICS       |  [ 🚀 Scan & Preview Plan ] [Configure]   |                 Media 12%, Other 7% ]|
|  Organized: 41 files  |                                                                                  |
|  Batches: 1           |  RECENT BATCH ACTIVITY                                                           |
|                       |  #batch-20261019-211421  | D:\Downloads  | 41 files | COMPLETED                  |
+----------------------------------------------------------------------------------------------------------+
| Ready.                                                                           [ Progressbar ]         |
+----------------------------------------------------------------------------------------------------------+
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
