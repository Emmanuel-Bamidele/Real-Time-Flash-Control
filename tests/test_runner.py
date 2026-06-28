import threading

import pytest

from flashcontrol.config import ConfigError, ExperimentConfig, HardwareConfig
from flashcontrol.core.runner import ExperimentRunner
from flashcontrol.hardware.simulated import SimulatedInstruments


class FakeClock:
    """Monotonic clock that advances a fixed step on every call."""

    def __init__(self, step=0.1):
        self.t = 0.0
        self.step = step

    def __call__(self):
        now = self.t
        self.t += self.step
        return now


def make_runner(**exp_kwargs):
    hw = HardwareConfig()
    defaults = dict(area=1.0, current_density=20.0, current_rate=10.0, holding_time=0.0)
    defaults.update(exp_kwargs)
    exp = ExperimentConfig(**defaults)
    sim = SimulatedInstruments(hw)
    return ExperimentRunner(
        exp, hw, sim, write_file=False, clock=FakeClock(step=0.1), sleep=lambda _s: None
    )


def test_run_completes_and_collects_samples():
    runner = make_runner()
    result = runner.run()
    assert result.completed is True
    assert result.stopped is False
    assert len(result.samples) > 0
    # Ramp time = 20 A / 10 A/s = 2 s; at 0.1 s steps that's ~20 samples.
    assert result.samples[-1].time_s <= runner.exp.execution_time()


def test_zero_current_has_no_division_by_zero():
    # The original could crash here: 0.0 / 0 when current == 0.
    runner = make_runner()
    runner.instruments.open()
    sample = runner.measure(0.0)
    assert sample.current_a == 0.0
    assert sample.resistance_ohm == 0.0  # guarded, not a ZeroDivisionError
    assert sample.voltage_measured == 0.0


def test_current_is_clamped_to_limit():
    # Hold past the ramp so the commanded current reaches and pins at the limit.
    runner = make_runner(holding_time=1.0)
    result = runner.run()
    limit = runner.exp.current_limit
    assert all(s.current_a <= limit + 1e-9 for s in result.samples)
    assert max(s.current_a for s in result.samples) == pytest.approx(limit)


def test_stop_event_cancels_run():
    runner = make_runner(holding_time=1000.0)  # would otherwise run very long
    stop_event = threading.Event()
    count = {"n": 0}

    def on_sample(_s):
        count["n"] += 1
        if count["n"] >= 3:
            stop_event.set()

    result = runner.run(stop_event=stop_event, on_sample=on_sample)
    assert result.stopped is True
    assert result.completed is False
    assert count["n"] == 3


def test_missing_output_dir_aborts_before_hardware():
    hw = HardwareConfig()
    exp = ExperimentConfig(area=1.0, current_density=10.0, current_rate=5.0, output_dir="")
    sim = SimulatedInstruments(hw)
    runner = ExperimentRunner(exp, hw, sim, write_file=True)
    with pytest.raises(ConfigError):
        runner.run()
    # Hardware was never opened.
    assert sim._opened is False


def test_async_run_reports_finish():
    runner = make_runner()
    done = threading.Event()
    captured = {}

    def on_finish(result):
        captured["result"] = result
        done.set()

    handle = runner.start_in_thread(on_finish=on_finish)
    assert done.wait(timeout=5)
    handle.join(timeout=5)
    assert captured["result"].error is None
    assert captured["result"].completed is True
