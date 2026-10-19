"""Automated PyInstaller build script to compile the Windows standalone executable."""

import sys
import shutil
import subprocess
from pathlib import Path


def build_windows_executable() -> None:
    """Build standalone Windows executable for the File Organizer application."""
    project_root = Path(__file__).resolve().parent.parent
    dist_dir = project_root / "dist"
    build_dir = project_root / "build"

    print("=" * 65)
    print("   BUILDING WINDOWS STANDALONE EXECUTABLE VIA PYINSTALLER")
    print("=" * 65)

    pyinstaller_exe = project_root / ".venv" / "Scripts" / "pyinstaller.exe"
    if not pyinstaller_exe.exists():
        pyinstaller_exe = Path(sys.executable).parent / "pyinstaller.exe"
    if not pyinstaller_exe.exists():
        pyinstaller_exe = Path("pyinstaller")

    entrypoint = project_root / "src" / "main.py"

    cmd = [
        str(pyinstaller_exe),
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name", "ContextAwareFileOrganizer",
        "--paths", str(project_root),
        "--hidden-import", "sqlite3",
        "--hidden-import", "tkinter",
        "--hidden-import", "hashlib",
        "--hidden-import", "shutil",
        str(entrypoint)
    ]

    print(f"Executing build command:\n{' '.join(cmd)}\n")
    res = subprocess.run(cmd, cwd=project_root)

    if res.returncode == 0:
        exe_path = dist_dir / "ContextAwareFileOrganizer.exe"
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print("\n" + "=" * 65)
            print("   BUILD SUCCESSFUL!")
            print(f"Executable output: {exe_path}")
            print(f"File size        : {size_mb:.2f} MB")
            print("=" * 65)
            return
    print("\n[ERROR] PyInstaller build failed with return code:", res.returncode)
    sys.exit(res.returncode)


if __name__ == "__main__":
    build_windows_executable()
