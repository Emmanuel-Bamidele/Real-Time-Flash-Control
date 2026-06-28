# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [2.0.0] — 2024

A full rewrite of the original single-file script into a tested, modular Python
package, while preserving the experiment behaviour and data format.

### Added
- **`flashcontrol` package** with decoupled layers:
  - `config` — `HardwareConfig` / `ExperimentConfig` dataclasses with validation
    and derived quantities (current/voltage scales, current limit, execution time).
  - `hardware` — an `Instruments` interface with a real NI-DAQ + Keithley backend
    and a driver-free `SimulatedInstruments` flash model, selected via
    `make_instruments(...)`.
  - `core` — `Sample` data model, a threaded `ExperimentRunner` (injectable
    clock/sleep, cooperative `Stop` via `threading.Event`), and a CSV writer.
  - `gui` — Tkinter app with an embedded matplotlib live plot, queue-based UI
    updates, modern theming, and an in-app Help window.
- **Simulation mode** — launch, demo, and test the app with no DAQ/Keithley
  attached (`--simulate-headless` for a no-GUI smoke test).
- **Hardware-readiness check** — `Instruments.probe()` plus header connection
  indicators (NI-DAQ / Keithley) and a "Check" action that lists DAQ devices and
  queries the Keithley `*IDN?` identity; full detail shown in the status bar.
- **In-app Help** — Setup, Hardware/Equipment, Citation and About tabs.
- **Test suite** (pytest) for config, runner, simulation and writer; **GitHub
  Actions CI** on Python 3.9 / 3.11 / 3.12 running tests + the headless simulation.
- Packaging (`pyproject.toml`, `requirements.txt`), `.gitignore`, a `SessionStart`
  hook, and a GUI preview image.

### Changed
- Entry point is now `main.py` / `python -m flashcontrol` (replaces the original
  `2023_08_26_FlashControl.py`).
- The header title now marks the app as **current-controlled**.
- The live plot is embedded in the window (`FigureCanvasTkAgg`) instead of the
  blocking `plt.pause` loop.
- Global state replaced by configuration dataclasses passed explicitly.

### Fixed
- Division by zero when computing resistance at `current == 0`.
- Acquisition no longer blocks the UI thread, so **Stop** is always responsive.
- A missing output folder now aborts cleanly *before* any hardware is touched
  (was a mid-run `NameError`).
- Output paths use `os.path.join` (was a hard-coded Windows `\\` separator).
- Current is always reset and instruments released on exit.
- The magic pyrometer constants `230` / `650` are now named config fields
  (`temp_scale`, `pyro_min_temp`).

## [1.0.0] — 2023-08

Initial release: a single-file Tkinter application
(`2023_08_26_FlashControl.py`) for current-controlled flash experiments with
NI-DAQ + Keithley acquisition and live plotting.

> The bundled `RealTimeFlashControl_Documentation.pdf` describes this 1.0
> release. For version 2.0 onward, see `README.md` and the in-app Help.
