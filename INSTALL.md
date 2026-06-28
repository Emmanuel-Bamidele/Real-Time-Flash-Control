# Installation

Three ways to get Real-Time Flash Control onto a computer, depending on who you
are. Most lab users want **Option A**.

> **Hardware note:** to drive the real rig you must also install the vendor
> runtimes — **NI-DAQmx** and **NI-VISA** (from National Instruments) — on the
> machine. These are separate from this software and cannot be bundled. The
> built-in **Simulation** mode needs none of them.

---

## Option A — Standalone application (no Python needed)

Best for lab PCs and non-developers.

1. Go to the project's **Releases** page on GitHub.
2. Download the file for your operating system:
   - Windows: `RealTimeFlashControl.exe`
   - macOS: `RealTimeFlashControl` (or the `.app`)
   - Linux: `RealTimeFlashControl`
3. Run it — double-click on Windows/macOS, or `./RealTimeFlashControl` on Linux.
   - Windows SmartScreen may warn about an unrecognised publisher: choose
     *More info → Run anyway*.
   - macOS Gatekeeper: right-click → *Open* the first time.
4. Leave **Simulate (no hardware)** ticked to try it immediately, or connect your
   rig, click **⟳ Check** in the header to confirm the NI-DAQ and Keithley are
   detected, then run.

## Option B — Install with pip (developers / scriptable)

Requires Python 3.9+.

```bash
# from a release wheel:
pip install flashcontrol-2.0.0-py3-none-any.whl

# or from source:
git clone https://github.com/Emmanuel-Bamidele/Real-Time-Flash-Control.git
cd Real-Time-Flash-Control
pip install -e ".[gui]"            # add ",hardware" for NI-DAQ + Keithley support
```

Then run:

```bash
flashcontrol                 # launch the GUI
flashcontrol-gui             # GUI without a console window (Windows)
python -m flashcontrol --simulate-headless   # no-GUI smoke test
```

On Linux you may need the Tk bindings: `sudo apt-get install python3-tk`.

## Option C — Build it yourself

Produce a wheel/sdist or a standalone executable.

```bash
pip install -e ".[gui,build]"     # add ",hardware" to bundle DAQ/Keithley wrappers

# wheel + source distribution -> dist/
python -m build

# standalone executable -> dist/RealTimeFlashControl[.exe]
pyinstaller flashcontrol.spec
```

Build the executable on the OS you want to target (PyInstaller does not
cross-compile). The release workflow in `.github/workflows/release.yml` does this
automatically for Windows, macOS and Linux when a `v*` tag is pushed.

---

## Verifying it works

```bash
python -m flashcontrol --simulate-headless
```

This runs a full simulated experiment and prints the final readings — no GUI and
no hardware required. For the GUI, launch it and run once in Simulate mode.
