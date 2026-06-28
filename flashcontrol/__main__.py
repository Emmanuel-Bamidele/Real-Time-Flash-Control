"""Console entry point: ``python -m flashcontrol`` or the ``flashcontrol`` script.

Supports a headless simulation run (no Tk/matplotlib) for smoke-testing the
acquisition pipeline, and otherwise launches the GUI.
"""

from __future__ import annotations

import argparse
import sys


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="flashcontrol", description=__doc__)
    parser.add_argument(
        "--simulate-headless",
        action="store_true",
        help="Run a short simulated experiment in the terminal (no GUI) and exit.",
    )
    args = parser.parse_args(argv)

    if args.simulate_headless:
        return _headless_demo()

    try:
        from .gui import run
    except Exception as exc:  # pragma: no cover - missing optional GUI deps
        print(f"GUI unavailable ({type(exc).__name__}: {exc}).", file=sys.stderr)
        print("Try: python -m flashcontrol --simulate-headless", file=sys.stderr)
        return 1
    run()
    return 0


def _headless_demo() -> int:
    from .config import ExperimentConfig, HardwareConfig
    from .core.runner import ExperimentRunner
    from .hardware import make_instruments

    hw = HardwareConfig()
    exp = ExperimentConfig(
        area=1.0, current_density=20.0, current_rate=10.0, holding_time=2.0, sampling_period=0.02
    )
    runner = ExperimentRunner(
        exp, hw, make_instruments(hw, simulate=True), write_file=False
    )
    print("Running simulated flash experiment…")
    result = runner.run(on_sample=lambda s: None)
    last = result.samples[-1]
    print(f"Acquired {len(result.samples)} samples over {result.elapsed:.2f} s.")
    print(
        f"Final: I={last.current_a:.2f} A, V={last.voltage_measured:.3f} V, "
        f"R={last.resistance_ohm:.3f} Ω, T={last.temperature_c:.1f} °C"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
