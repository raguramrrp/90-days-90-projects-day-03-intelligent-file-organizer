# Development Notes & Engineering Decisions

This document outlines key technical decisions, performance optimizations, edge-case safety safeguards, and trade-offs made while building the **Context-Aware Desktop File Organization Automation Engine**.

---

## 1. Technical Stack Selection

### Why Tkinter & Python Standard Library?
- **Zero Heavyweight Runtime Dependencies**: A desktop utility for file organization must launch instantly and not require Node.js, Electron, or a browser runtime consuming 500MB of RAM.
- **Portability on Windows**: Tkinter and Tcl/Tk are bundled directly with standard Python on Windows.
- **Single Executable Compilability**: Python + Tkinter packages cleanly into a self-contained 13MB standalone `.exe` using PyInstaller, running without requiring Python installed on the target machine.

---

## 2. Algorithmic Optimizations: Two-Tier Duplicate Detection

### The Problem:
Computing cryptographic hashes (SHA-256/MD5) across thousands of user files (some several gigabytes in size) causes heavy disk I/O bottlenecks and high CPU usage.

### The Optimization:
1. **Tier 1 — O(N) File Size Bucketing**:
   - Query file size metadata from `stat()`.
   - Files with unique byte counts cannot be duplicates. Over 90% of files in typical directories have distinct sizes and are instantly filtered out without opening their file descriptors.
2. **Tier 2 — Streaming SHA-256 Hashing**:
   - Only files that share an identical byte length with at least one other candidate are subjected to cryptographic hashing.
   - Files are read in buffered 64KB chunks (`f.read(65536)`) to keep memory footprint flat regardless of whether the file is 10 KB or 10 GB.

---

## 3. Filesystem Safety & Edge Case Handling

### 1. In-Place Target Directory Collision Prevention
When the user organizes a folder in-place (e.g. `source_dir == target_dir`), the scanner automatically excludes pre-existing or target category subdirectories (`Documents`, `Images`, `_Duplicates`, etc.) from recursive scans to prevent endless loop nesting.

### 2. Compound Extension Resolution
Files like `dataset.tar.gz` or `script.user.js` typically lose their compound suffix with naive `Path.suffix` splitting (which only yields `.gz` or `.js`). The scanner checks against known compound suffixes first, ensuring `.tar.gz` files route correctly to `Archives/`.

### 3. Collision Resolution Strategy
When moving `invoice.pdf` into a folder that already contains `invoice.pdf`:
- Default strategy: `rename`.
- An incremental loop calculates `invoice (1).pdf`, `invoice (2).pdf`, etc.
- To prevent batch race conditions where multiple source files could collide with the same newly generated candidate name, the engine maintains an in-memory `claimed_destinations` set during plan generation.

### 4. Non-Destructive Operations & Transaction Reversibility
- Files are never deleted or truncated.
- The `operations` table stores exact source and destination absolute paths.
- Rollback processes operations in reverse order, recreating parent directories if necessary, restoring the filesystem to its exact state prior to batch execution.

---

## 4. Database Concurrency & Performance

- **Write-Ahead Logging (WAL)**: Enabled via `PRAGMA journal_mode = WAL;` to prevent database locks when the UI reads stats while a background thread logs operations.
- **Foreign Keys**: Enabled via `PRAGMA foreign_keys = ON;` to maintain relational integrity between batches and individual operations.
- **Indexes**: Added on `operations(batch_id)`, `operations(status)`, `batches(created_at)`, and `rules(priority)` to ensure sub-millisecond query responses even with tens of thousands of logged operations.
