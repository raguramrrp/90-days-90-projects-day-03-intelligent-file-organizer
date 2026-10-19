# Benchmark Dataset Documentation — Sample Downloads Clutter

This directory contains the synthetic benchmark dataset used to evaluate, demonstrate, and test the **Context-Aware Desktop File Organization Automation** engine.

---

## 📁 Dataset Overview

The dataset models a typical chaotic user Downloads directory accumulated over 4–6 months of activity. It includes diverse real-world file formats, date variations, naming conventions, and deliberate duplicate clusters.

- **Primary Folder**: `data/sample_clutter/`
- **Total Synthetic Files**: 41 files
- **Total Redundant Clones**: 6 verified duplicates
- **License**: Public Domain (CC0) / Synthetic Open Data
- **Data Privacy**: 100% synthetic mock byte streams; contains zero personal, sensitive, or external proprietary data.

---

## 🗂️ File Distribution by Category

| Category | File Extensions | Example Files |
| :--- | :--- | :--- |
| **Finances / Invoices** | `.pdf`, `.jpg` | `Invoice_2026_098.pdf`, `AWS_Billing_Invoice_Sept2026.pdf`, `Hardware_Store_Receipt.jpg` |
| **Screenshots** | `.png`, `.jpg` | `Screenshot_2026-10-01_143022.png`, `Screenshot_Error_Console.png` |
| **Career / Resumes** | `.pdf`, `.docx` | `Resume_Raguram_AI_Engineer.pdf`, `CV_DataScientist_2026.docx` |
| **Documents** | `.pdf`, `.docx`, `.txt`, `.md`, `.tex` | `Machine_Learning_Lecture_Notes.pdf`, `meeting_notes_20261015.txt`, `quick_thoughts.md` |
| **Spreadsheets & Data**| `.csv`, `.xlsx`, `.tsv` | `customer_churn_analysis.csv`, `sales_forecast_q4_2026.xlsx`, `product_metrics.tsv` |
| **Images** | `.jpg`, `.png`, `.svg`, `.webp` | `vacation_beach_sunset.jpg`, `architecture_diagram.svg`, `profile_avatar_headshot.png` |
| **Audio & Video** | `.mp3`, `.wav`, `.mp4`, `.mkv` | `podcast_interview_ep42.mp3`, `demo_screen_recording.mp4`, `keynote_presentation_stream.mkv` |
| **Archives** | `.zip`, `.tar.gz`, `.7z` | `project_source_archive.zip`, `dataset_training_split.tar.gz`, `developer_tools_bundle.7z` |
| **Code & Scripts** | `.py`, `.js`, `.css`, `.sql` | `data_pipeline.py`, `frontend_bundle.js`, `schema_migrations.sql` |
| **Software Installers**| `.exe`, `.msi` | `VSCodeUserSetup_x64_1.94.exe`, `DockerDesktop_Installer.msi` |
| **Presentations** | `.pptx` | `Pitch_Deck_Hackathon_2026.pptx` |

---

## 🔄 Duplicate Clusters

The generator injects 6 binary duplicates to test cryptographic hash detection:
1. `AWS_Billing_Invoice_Sept2026 (Copy).pdf` (Duplicate of `AWS_Billing_Invoice_Sept2026.pdf`)
2. `download (1).pdf` (Duplicate of `AWS_Billing_Invoice_Sept2026.pdf`)
3. `vacation_beach_sunset_backup.jpg` (Duplicate of `vacation_beach_sunset.jpg`)
4. `IMG_20261019_001.jpg` (Duplicate of `vacation_beach_sunset.jpg`)
5. `churn_backup.csv` (Duplicate of `customer_churn_analysis.csv`)
6. `Screenshot_duplicate.png` (Duplicate of `Screenshot_2026-10-01_143022.png`)

---

## 🛠️ Regenerating the Dataset

To re-create or reset the synthetic test data at any time, run:

```bash
.\.venv\Scripts\python scripts\generate_sample_data.py
```
