"""Sample clutter dataset generator for benchmarking and demonstrating desktop file organization."""

from __future__ import annotations

import os
import shutil
import random
from datetime import datetime, timedelta
from pathlib import Path


def generate_sample_downloads_clutter(target_dir: Path | str, file_count: int = 40) -> Path:
    """Create a realistic cluttered downloads folder containing varied file types, dates, and duplicates."""
    root = Path(target_dir).resolve()
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)

    now = datetime.now()

    # Sample file definitions: (filename, content_bytes, days_ago)
    sample_templates = [
        # Invoices and Receipts (triggers custom rules)
        ("Invoice_2026_098.pdf", b"%PDF-1.4 Invoice #098 Total: $1,450.00 Vendor: CloudCorp", 12),
        ("AWS_Billing_Invoice_Sept2026.pdf", b"%PDF-1.4 Amazon Web Services Cloud Compute Invoice $342.18", 25),
        ("Uber_Ride_Receipt_Oct12.pdf", b"%PDF-1.4 Uber Technologies Trip Receipt #4982 Amount: $24.50", 7),
        ("Hardware_Store_Receipt.jpg", b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01Store Receipt $89.20", 3),

        # Screenshots (triggers custom rule)
        ("Screenshot_2026-10-01_143022.png", b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR Mock Screenshot Dashboard", 18),
        ("Screenshot_Error_Console.png", b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR Mock Screenshot Bug Report", 5),
        ("Screenshot_Design_Mockup.jpg", b"\xFF\xD8\xFF\xE0\x00\x10JFIF UI Layout v2 Mockup", 14),

        # Resumes & Careers (triggers custom rule)
        ("Resume_Raguram_AI_Engineer.pdf", b"%PDF-1.4 Resume - Raguram R R P - AI & Data Science Engineer", 45),
        ("CV_DataScientist_2026.docx", b"PK\x03\x04 Curriculum Vitae - Research & Machine Learning", 60),

        # General Documents (triggers Document category)
        ("Machine_Learning_Lecture_Notes.pdf", b"%PDF-1.4 Chapter 4: Gradient Boosting & Neural Architectures", 30),
        ("Project_Proposal_Draft_v3.docx", b"PK\x03\x04 Comprehensive Project Technical Architecture Proposal", 15),
        ("meeting_notes_20261015.txt", b"Weekly Engineering Sync: Focus on Day 3 File Automation project", 4),
        ("quick_thoughts.md", b"# Antigravity Pairing Notes\nNext step is Tkinter implementation.", 2),
        ("research_paper_draft.tex", b"\\documentclass{article}\\begin{document}Autonomous Agents\\end{document}", 90),

        # Spreadsheets & Datasets (triggers Spreadsheets & Data category)
        ("customer_churn_analysis.csv", b"customer_id,tenure,monthly_charges,churn\n101,12,65.4,0\n102,4,89.1,1\n103,36,45.0,0", 8),
        ("sales_forecast_q4_2026.xlsx", b"PK\x03\x04 Mock Q4 Financial Forecasting Data Tables", 20),
        ("product_metrics.tsv", b"metric_id\tmetric_name\tvalue\n1\tdaus\t14200\n2\tretention\t0.74", 16),

        # Images (triggers Images category)
        ("vacation_beach_sunset.jpg", b"\xFF\xD8\xFF\xE0\x00\x10JFIF Sunset at Gokarna Beach 2026", 110),
        ("profile_avatar_headshot.png", b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR Developer Avatar", 40),
        ("architecture_diagram.svg", b"<svg xmlns='http://www.w3.org/2000/svg'><circle cx='50' cy='50' r='40'/></svg>", 9),
        ("team_hackathon_celebration.webp", b"RIFF\x00\x00\x00\x00WEBPVP8 Hackathon Winners 2026", 1),

        # Audio & Video (triggers Audio & Video categories)
        ("podcast_interview_ep42.mp3", b"ID3\x03\x00\x00\x00 AI Systems and Automation Deep Dive Podcast", 50),
        ("guitar_acoustic_sample.wav", b"RIFF\x00\x00\x00\x00WAVEfmt Acoustic Guitar Riff Strum", 22),
        ("demo_screen_recording.mp4", b"\x00\x00\x00\x18ftypmp42 Product Demo Screencast MP4 Recording", 6),
        ("keynote_presentation_stream.mkv", b"\x1a\x45\xdf\xa3 Matroska Keynote Video Recording", 75),

        # Archives & Compressed (triggers Archives category)
        ("project_source_archive.zip", b"PK\x03\x04 Zip Archive containing project source code snapshots", 35),
        ("dataset_training_split.tar.gz", b"\x1f\x8b\x08\x00 Gzip Archive containing annotated dataset splits", 65),
        ("developer_tools_bundle.7z", b"7z\xbc\xaf\x27\x1c 7-Zip Compressed Utility Bundle", 140),

        # Code & Scripts (triggers Code & Scripts category)
        ("data_pipeline.py", b"import pandas as pd\ndef run(): print('Pipeline executed successfully')\n", 10),
        ("frontend_bundle.js", b"console.log('App initialized on client'); window.onload = () => {};", 11),
        ("styles_theme.css", b":root { --primary: #89b4fa; --bg: #1e1e2e; } body { margin: 0; }", 11),
        ("schema_migrations.sql", b"CREATE TABLE users (id SERIAL PRIMARY KEY, username VARCHAR(50));", 28),

        # Installers & Executables (triggers Installers category & rule)
        ("VSCodeUserSetup_x64_1.94.exe", b"MZ\x90\x00\x03\x00\x00\x00 Mock VSCode Windows Installer Executable", 80),
        ("DockerDesktop_Installer.msi", b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1 Mock Windows MSI Package", 95),

        # Presentations
        ("Pitch_Deck_Hackathon_2026.pptx", b"PK\x03\x04 Pitch Deck: Intelligent Desktop File Automation", 13),
    ]

    created_paths = []

    for name, content, days_ago in sample_templates:
        fpath = root / name
        fpath.write_bytes(content)

        # Set fake historical timestamps
        mod_time = (now - timedelta(days=days_ago, hours=random.randint(1, 12))).timestamp()
        os.utime(fpath, (mod_time, mod_time))
        created_paths.append(fpath)

    # Inject deliberate binary duplicates to test and demonstrate duplicate detection
    dup_specs = [
        # Duplicate of AWS billing invoice
        ("AWS_Billing_Invoice_Sept2026.pdf", "AWS_Billing_Invoice_Sept2026 (Copy).pdf", 25),
        ("AWS_Billing_Invoice_Sept2026.pdf", "download (1).pdf", 25),

        # Duplicate of vacation photo
        ("vacation_beach_sunset.jpg", "vacation_beach_sunset_backup.jpg", 110),
        ("vacation_beach_sunset.jpg", "IMG_20261019_001.jpg", 110),

        # Duplicate of customer churn dataset
        ("customer_churn_analysis.csv", "churn_backup.csv", 8),

        # Duplicate of screenshot
        ("Screenshot_2026-10-01_143022.png", "Screenshot_duplicate.png", 18),
    ]

    for original_name, duplicate_name, days_ago in dup_specs:
        orig = root / original_name
        if orig.exists():
            dup_path = root / duplicate_name
            shutil.copy2(orig, dup_path)
            mod_time = (now - timedelta(days=days_ago, minutes=random.randint(5, 60))).timestamp()
            os.utime(dup_path, (mod_time, mod_time))
            created_paths.append(dup_path)

    print(f"Generated {len(created_paths)} realistic sample clutter files in: {root}")
    return root


if __name__ == "__main__":
    out_dir = Path(__file__).resolve().parent.parent / "data" / "sample_clutter"
    generate_sample_downloads_clutter(out_dir)
