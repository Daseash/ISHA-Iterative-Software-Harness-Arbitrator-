#!/usr/bin/env python3
"""
ISHA Dashboard launcher — delegates to src/dashboard/app.py.

    streamlit run dashboard.py        # equivalent
    streamlit run src/dashboard/app.py
"""


import runpy
from pathlib import Path

runpy.run_path(str(Path(__file__).resolve().parent / "src" / "dashboard" / "app.py"), run_name="__main__")
