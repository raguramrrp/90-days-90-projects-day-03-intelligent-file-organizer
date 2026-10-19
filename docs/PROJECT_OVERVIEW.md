# Project Overview — Context-Aware Desktop File Organization Automation

**Challenge**: Day 3 of 90 Days – 90 Projects Challenge  
**Professional Title**: Context-Aware Desktop File Organization Automation  
**Author**: Final-Year B.Tech Artificial Intelligence & Data Science Student  
**Target Domain**: Automation & Desktop Systems Engineering  
**Difficulty**: Beginner | Build Duration: 3–4 Hours  

---

## 1. Problem Statement

User download folders and desktop surfaces rapidly deteriorate into digital clutter heaps over weeks of routine computer usage. Users frequently accumulate:
- Mixed media files (screenshots, video recordings, high-res photos, podcasts).
- Documents, resumes, tax receipts, and enterprise invoices.
- Compressed multi-part archives and software installation packages.
- Redundant and duplicate downloads of identical assets wasting local disk storage.
- Loose source code files, data exports (`.csv`, `.tsv`, `.parquet`), and log artifacts.

Manually sorting, classifying, and filing hundreds of loose files into coherent nested directories is time-consuming, prone to human error, and poses high risk of accidental overwrites or file loss.

---

## 2. Solution & Value Proposition

**Context-Aware Desktop File Organizer** delivers an automated, deterministic, and safe solution:
1. **Multi-Faceted Classification**: Groups files by semantic file extension categories, user-defined regex/wildcard rules, and hierarchical temporal dates.
2. **Two-Tier Cryptographic Deduplication**: Employs rapid file size filtering followed by streaming SHA-256 chunked hashing to isolate true duplicate clones without reading unique files from disk.
3. **Interactive Simulation (Preview Before Move)**: Provides a transparent dry-run inspection table detailing proposed source and target paths, rule tags, collision handling, and size impact.
4. **Collision & Conflict Prevention**: Auto-appends incremental version indexes (e.g. `document (1).pdf`) or skips existing target files to eliminate accidental data loss.
5. **Enterprise Reversibility**: Maintains a local SQLite audit database (`batches` and `operations` tables) enabling **one-click rollback** of any executed batch.

---

## 3. Scope & MVP Boundaries

### Within Scope (Delivered MVP)
- Full-featured, responsive Tkinter graphical user interface with 4 dedicated workflow tabs.
- Full-featured headless command-line interface (CLI) for scripting and automation.
- Priority-ordered rule engine with custom modal rule creation (patterns, extensions, size thresholds, age).
- Date grouping by Year, Year-Month (`YYYY-MM`), or Full Date (`YYYY-MM-DD`).
- Duplicate detection, duplicate quarantine, and disk space reclamation reporting.
- Reversible transaction audit trail in SQLite with batch undo and CSV/JSON export.
- Standalone compiled Windows `.exe` executable via PyInstaller.
- Synthetic downloads clutter dataset generator with 41 realistic benchmark files.
- Automated test suite (24 unit and integration tests passing at 100%).

### Future Upgrade Path
- Content-based machine learning classification (TF-IDF / embeddings for PDF document topic clustering).
- Windows Background File System Watcher (`watchdog`) for instant hands-free download sorting.
- Cloud storage folder sync (Google Drive, OneDrive, Dropbox).
