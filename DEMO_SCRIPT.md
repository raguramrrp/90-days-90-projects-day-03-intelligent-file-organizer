# 60–120 Second Portfolio Demonstration Script

**Project Title**: Context-Aware Desktop File Organization Automation Engine  
**Presenter**: Final-Year AI & Data Science Candidate  
**Target Audience**: Technical Recruiters, Hiring Managers, Hackathon Judges  
**Duration**: ~90 Seconds  

---

### [00:00 – 00:15] The Hook & Problem Statement
> *"Hello everyone! Like most engineers and power users, my Downloads and Desktop directories easily accumulate hundreds of cluttered files every month—invoices, screenshots, datasets, scripts, and duplicate installers.*
> *Today, I'm presenting **Context-Aware Desktop File Organizer**, an autonomous desktop automation engine built with Python, Tkinter, and SQLite that classifies, deduplicates, and organizes cluttered directories with deterministic rule execution and reversible audit rollback."*

---

### [00:15 – 00:35] Folder Selection & Strategy Setup
*(Action: Open application via `run.bat` or double-click `dist\ContextAwareFileOrganizer.exe`)*
> *"Let's select our messy demo directory or hit the quick 'Downloads' preset. Notice our strategic controls: we can enable temporal clustering by year-month (`YYYY-MM`), set collision handling to auto-rename with an index `(1)` to avoid data loss, and quarantine duplicate files.*
> *Before touching a single file on disk, safety is paramount. I'll click **'Scan Folder & Generate Preview'**."*

---

### [00:35 – 00:55] Plan Simulation & Duplicate Detection
*(Action: App switches to Tab 3: Preview & Organize)*
> *"The engine scans the entire tree in milliseconds. It performs two-tier duplicate detection: fast size bucketing followed by streaming SHA-256 cryptographic hashing. It immediately flags 6 redundant duplicate files wasting disk space.*
> *In the preview table, we see clear proposed routes: `Invoice_2026_098.pdf` matches our priority rule for Finances, `Screenshot_2026-10-01.png` is routed to Screenshots, and datasets go to Spreadsheets. Users can search or uncheck any item to exclude it from the batch."*

---

### [00:55 – 01:15] One-Click Execution & Verification
*(Action: Click '🚀 Execute Organization Now', confirm dialog, and click 'Yes' to open organized directory in Windows Explorer)*
> *"I hit **'Execute Organization'**. In less than two seconds, 41 files are safely moved into categorized semantic folders. Windows Explorer opens, showing a clean, structured workspace."*

---

### [01:15 – 01:35] Enterprise Reversibility & Audit Rollback
*(Action: Switch to Tab 4: History & Undo, select the batch, click '↩️ Undo / Rollback Selected Batch')*
> *"What sets this apart from basic tutorial scripts is full transaction auditability. Every operation is recorded in SQLite with source path, destination, timestamp, and SHA-256 hash. If a user ever makes a mistake, they simply select the batch and click **'Undo / Rollback'**. Instantly, all 41 files are restored to their exact original locations. We can also export full compliance audit logs to CSV or JSON."*

---

### [01:35 – 01:50] Architectural Robustness & Headless Automation
*(Action: Show command line with `src/main.py --stats` or test suite)*
> *"Under the hood, the engine features 24 automated unit and integration tests passing at 100%, a standalone compiled Windows `.exe`, and a full headless CLI interface that can be scheduled via Windows Task Scheduler. Thank you!"*
