# Quickstart Guide — Context-Aware Desktop File Organizer

Get up and running with the **Context-Aware Desktop File Organization Automation Engine** on Windows in under 2 minutes.

---

## ⚡ Method 1: One-Click Windows Automated Setup (Recommended)

1. **Double-click `setup.bat`**  
   - Automatically detects your Python 3.10+ runtime.
   - Creates a dedicated virtual environment in `.venv/`.
   - Installs all dependencies (`pytest`, `pyinstaller`, `pillow`).
   - Initializes directories and generates 41 synthetic clutter test files in `data/sample_clutter/`.

2. **Launch the Graphical User Interface**  
   ```cmd
   run.bat
   ```

3. **Run the Automated Test Suite**  
   ```cmd
   test.bat
   ```

4. **Compile Standalone Windows `.exe`**  
   ```cmd
   build_exe.bat
   ```

---

## 🛠️ Method 2: Manual Setup via PowerShell / Command Prompt

If you prefer executing commands manually:

```powershell
# 1. Navigate to the project root directory
cd "d:\90 days\90-days-90-projects-day-03-intelligent-file-organizer"

# 2. Create Python virtual environment
python -m venv .venv

# 3. Activate the virtual environment
.\.venv\Scripts\Activate.ps1
# (or in cmd.exe: .\.venv\Scripts\activate.bat)

# 4. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 5. Generate benchmark sample clutter files
python scripts/generate_sample_data.py

# 6. Launch the Desktop Application
python src/main.py --gui
```

---

## 💻 Method 3: Headless Command-Line Interface (CLI)

The application can also run headlessly without a display, making it ideal for automation scripts and Windows Task Scheduler:

```bash
# Display system metrics and audit history
.\.venv\Scripts\python src/main.py --stats

# List all active organization rules in priority order
.\.venv\Scripts\python src/main.py --list-rules

# Run a dry-run simulation on the sample clutter folder (No changes on disk)
.\.venv\Scripts\python src/main.py --dry-run data/sample_clutter

# Run dry-run with temporal date grouping (YYYY-MM)
.\.venv\Scripts\python src/main.py --dry-run data/sample_clutter --date-grouping year_month

# Execute actual organization on the clutter folder
.\.venv\Scripts\python src/main.py --organize data/sample_clutter

# Rollback an executed batch using its Batch ID
.\.venv\Scripts\python src/main.py --undo <BATCH_ID>

# Export audit operations log to CSV
.\.venv\Scripts\python src/main.py --export-csv audit_export.csv
```
