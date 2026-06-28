# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — builds a standalone Real-Time Flash Control application.

Produces a single self-contained executable (no Python install required) for the
host operating system:

    pip install -e ".[gui,build]"      # add ",hardware" to bundle DAQ/Keithley support
    pyinstaller flashcontrol.spec
    # -> dist/RealTimeFlashControl  (or .exe on Windows / .app on macOS)

Note: bundling `nidaqmx`/`pyvisa` only includes the Python wrappers. Driving real
instruments still requires the vendor runtimes (NI-DAQmx and NI-VISA) installed
on the machine. Simulation mode works fully standalone.
"""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Always include the app and the matplotlib Tk backend.
hidden = collect_submodules("flashcontrol")
hidden += ["matplotlib.backends.backend_tkagg"]
datas = collect_data_files("matplotlib")

# Include the optional hardware wrappers only if they were installed at build time.
for optional in ("nidaqmx", "pyvisa"):
    try:
        __import__(optional)
        hidden += collect_submodules(optional)
    except Exception:
        pass

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="RealTimeFlashControl",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI application — no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
