#!/usr/bin/env python3
"""Launcher for the Real-Time Flash Control application.

This replaces the original ``2023_08_26_FlashControl.py`` single-file script.
The implementation now lives in the :mod:`flashcontrol` package.

Usage::

    python main.py                       # launch the GUI
    python -m flashcontrol               # equivalent
    python -m flashcontrol --simulate-headless   # quick no-GUI smoke test
"""

from flashcontrol.__main__ import main

if __name__ == "__main__":
    raise SystemExit(main())
