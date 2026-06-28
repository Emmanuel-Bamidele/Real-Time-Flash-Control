# Contributing & developer notes

Thanks for your interest in improving Real-Time Flash Control. This document
covers the architecture and the common extension points.

## Setup

```bash
pip install -e ".[dev]"     # core + tests (no GUI/hardware needed)
pip install -e ".[gui]"     # add matplotlib for the GUI
pip install -e ".[hardware]" # add nidaqmx + pyvisa to drive real instruments
```

Run the checks:

```bash
pytest -q
python -m flashcontrol --simulate-headless
```

## Architecture

The package is layered so the experiment logic is testable without a GUI or
hardware. The dependency direction is strictly **downward**:

```
gui  ──▶ core ──▶ hardware ──▶ config
                      └────────▶ config
```

- `config` — pure dataclasses + validation. No I/O.
- `hardware` — the `Instruments` interface and its backends. **Only**
  `hardware/nidaq.py` imports `nidaqmx` / `pyvisa`, and it does so lazily.
- `core` — the `ExperimentRunner` and data model. Imports no Tk, matplotlib or
  drivers, so it runs in CI against the simulation.
- `gui` — Tkinter + matplotlib. Imported lazily via `flashcontrol.gui.run`.

Key design choices:

- **Injectable clock/sleep** in `ExperimentRunner` make the acquisition loop
  deterministic in tests (no real waiting, no wall-clock flakiness).
- **Cooperative cancellation** via a `threading.Event` keeps Stop responsive.
- **Validation before hardware** — `runner.validate()` runs before anything is
  opened, so bad input fails fast and safe.

## Adding a new instrument backend

1. Subclass `flashcontrol.hardware.base.Instruments` and implement every
   abstract method, including `probe()` (return one `InstrumentStatus` per
   instrument so the GUI's readiness indicators work).
2. Wire it into `flashcontrol.hardware.make_instruments(...)`.
3. Add tests against it the way `tests/test_simulated.py` does — no real
   hardware required if you mock or simulate.

## Adding a plot channel or readout

Channels are defined once in `core/sample.py` (`Sample`, `COLUMN_NAMES`,
`COLUMN_UNITS`) and mapped to plot labels in `gui/plot.py` (`CHANNELS`). Add the
field in both places; the CSV writer and live plot pick it up automatically.

## Style

- Match the surrounding code: type hints, module/class docstrings, and comments
  that explain *why* rather than *what*.
- Keep `config`, `core` and `hardware` free of Tk / matplotlib / driver imports
  so the test suite keeps running everywhere.
- Run `pytest -q` before opening a pull request.

## Releasing

Update `CHANGELOG.md` and the version in `pyproject.toml` and
`flashcontrol/__init__.py` together.
