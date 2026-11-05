#!/usr/bin/env python3
"""
ISHA Dashboard launcher.

    streamlit run scripts/run_dashboard.py
    streamlit run src/dashboard/app.py       # equivalent
"""

import runpy
from pathlib import Path

runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "src" / "dashboard" / "app.py"),
    run_name="__main__",
)
