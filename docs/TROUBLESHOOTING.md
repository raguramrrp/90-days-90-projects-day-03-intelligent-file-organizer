# Troubleshooting Guide — Context-Aware Desktop File Organizer

This guide provides fast solutions for common operational issues, filesystem permission errors, and configuration challenges on Windows.

---

## 1. Filesystem Permission & Lock Errors

### Symptom: `PermissionError: [WinError 32] The process cannot access the file because it is being used by another process`
- **Cause**: The file you are trying to move is currently open in another program (e.g., an active PDF in Adobe Acrobat, a Word document open in Microsoft Word, an incomplete download in Chrome/Edge, or an active torrent client).
- **Solution**:
  1. Close the application currently holding the file open.
  2. If a download is in progress (files ending in `.crdownload` or `.part`), wait for the download to finish before running organization.
  3. The File Organizer logs this specific file as `FAILED` in the database without halting the rest of the batch. You can re-run organization once the lock is released.

---

## 2. Python Environment & Path Errors

### Symptom: `ModuleNotFoundError: No module named 'src'`
- **Cause**: Running Python scripts without the repository root added to `PYTHONPATH`.
- **Solution**:
  - Always run via `run.bat` or `test.bat`, which automatically configure `PYTHONPATH`.
  - Or manually set it in PowerShell:
    ```powershell
    $env:PYTHONPATH = "d:\90 days\90-days-90-projects-day-03-intelligent-file-organizer"
    ```

### Symptom: `Python is not recognized as an internal or external command`
- **Cause**: Python is not registered on your Windows system PATH.
- **Solution**:
  1. Re-run the official Python Windows installer from [python.org](https://www.python.org/).
  2. Check the box: **"Add Python to PATH"** during installation.

---

## 3. Rollback / Undo Warnings

### Symptom: `Organized file no longer found at: <Path>` during Rollback
- **Cause**: The file was moved, renamed, or deleted manually in Windows Explorer after the organization batch took place.
- **Solution**: The engine will restore all other files in the batch safely and log a warning for the missing file. Check your Windows Recycle Bin if the file was accidentally deleted.

---

## 4. Screenshot Capture on Headless / Remote Desktops

### Symptom: `OSError: screen grab failed` when running `scripts/capture_screenshots.py`
- **Cause**: Pillow's `ImageGrab.grab()` requires an active graphical display device context. This occurs when executing over headless SSH, non-interactive CI environments, or locked Windows RDP sessions.
- **Solution**: Run `capture_screenshots.py` directly from an interactive, unlocked Windows desktop command prompt.
