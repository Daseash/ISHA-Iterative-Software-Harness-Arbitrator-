#!/usr/bin/env python3
"""install.py - one-command ISHA installer (cross-platform).

Usage:
    python install.py

Creates .venv/ in the repo root, installs the prebuilt wheel from dist/
(falling back to the source tree), copies .env.example to .env, and runs
`isha --help` as a self-check.

Windows:  powershell -NoProfile -ExecutionPolicy Bypass -File install.ps1
Linux/macOS:  bash install.sh
Anywhere:   python install.py
"""

import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
VENV = REPO / ".venv"


def run(*cmd, **kw):
    print(f"$ {' '.join(str(c) for c in cmd)}")
    return subprocess.run([str(c) for c in cmd], check=True, **kw)


def main():
    if sys.version_info < (3, 10):
        sys.exit(f"Python 3.10+ required, found {sys.version.split()[0]}")

    if not VENV.exists():
        print(f"Creating {VENV} ...")
        run(sys.executable, "-m", "venv", VENV)

    py = VENV / ("Scripts" if sys.platform == "win32" else "bin") / "python"
    isha = VENV / ("Scripts" if sys.platform == "win32" else "bin") / "isha"

    print("Upgrading pip ...")
    run(py, "-m", "pip", "install", "--quiet", "--upgrade", "pip")

    wheel = sorted((REPO / "dist").glob("isha_fix-*.whl"))
    target = wheel[-1] if wheel else REPO
    if wheel:
        print(f"Installing {wheel[-1].name} ...")
    else:
        print("No wheel in dist/ - installing from source tree ...")
    print("First run downloads dependencies (a few hundred MB; docling pulls torch/CUDA).")
    run(py, "-m", "pip", "install", "--quiet", str(target))

    env_dst = REPO / ".env"
    if not env_dst.exists():
        shutil.copy2(REPO / ".env.example", env_dst)
        print(f"Created {env_dst} - add your GROQ_API_KEY / GOOGLE_API_KEY")

    print("Self-check: isha --help")
    run(isha, "--help")

    print()
    print("Done. Next steps:")
    print(f"  1. edit {env_dst}            # add your free API keys")
    print(f"  2. {isha} doctor             # verify providers")
    print(f"  3. {isha} fix --repo <path-or-url> --issue '...' --apply")


if __name__ == "__main__":
    main()
