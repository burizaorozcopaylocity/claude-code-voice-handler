#!/usr/bin/env python3
"""Redirect to hook_entry.py - keeps hooks working while avoiding package shadowing."""
import runpy
import sys
from pathlib import Path

# Run hook_entry.py with the same arguments
hook_entry = Path(__file__).parent / "hook_entry.py"
sys.argv[0] = str(hook_entry)
runpy.run_path(str(hook_entry), run_name="__main__")
