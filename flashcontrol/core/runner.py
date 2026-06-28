"""The experiment runner - the acquisition loop, free of GUI and hardware.

:class:`ExperimentRunner` ties a :class:`~flashcontrol.config.ExperimentConfig`
and :class:`~flashcontrol.config.HardwareConfig` to an
:class:`~flashcontrol.hardware.base.Instruments` backend and produces
:class:`~flashcontrol.core.sample.Sample` rows.

Design choices that fix bugs in the original and make it testable:

* The clock and sleep are injected (default :func:`time.monotonic` /
  :func:`time.sleep`), so tests drive the loop deterministically with no real
  waiting and no wall-clock flakiness.
* Cooperative cancellation via a :class:`threading.Event` - so a "Stop" button
  actually stops the loop (the original blocked the GUI thread entirely).
* All validation happens *before* any hardware is touched, so a missing output
  folder aborts cleanly instead of crashing mid-run with a ``NameError``.
* Resistance is guarded against division by zero at ``current == 0``.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from ..config import ExperimentConfig, HardwareConfig
from ..hardware.base import Instruments
from .sample import Sample
from .writer import CsvDataWriter

SampleCallback = Callable[[Sample], None]
FinishCallback = Callable[["RunResult"], None]


@dataclass
class RunResult:
    """Outcome of a run."""

    samples: List[Sample] = field(default_factory=list)
    elapsed: float = 0.0
    completed: bool = False  # reached the full execution time
    stopped: bool = False  # cancellation was requested
    error: Optional[BaseException] = None


@dataclass
class RunHandle:
    """Handle to an in-progress asynchronous run."""

    thread: threading.Thread
    stop_event: threading.Event

    def stop(self) -> None:
        """Request cancellation; the loop ends after its current sample."""
        self.stop_event.set()

    def join(self, timeout: Optional[float] = None) -> None:
        self.thread.join(timeout)

    def is_running(self) -> bool:
        return self.thread.is_alive()


class ExperimentRunner:
    def __init__(
        self,
        experiment: ExperimentConfig,
        hardware: HardwareConfig,
        instruments: Instruments,
        *,
        write_file: bool = True,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.exp = experiment
        self.hw = hardware
        self.instruments = instruments
        self.write_file = write_file
        self._clock = clock
        self._sleep = sleep

    # -- validation -------------------------------------------------------
    def validate(self) -> None:
        """Validate everything that must hold before touching hardware."""
        self.hw.validate()
        self.exp.validate()
        self.exp.check_against_supply(self.hw)
        if self.write_file and not self.exp.output_dir:
            from ..config import ConfigError

            raise ConfigError("Select an output folder before starting a run.")

    # -- single measurement ----------------------------------------------
    def measure(self, elapsed: float) -> Sample:
        """Command the current for ``elapsed`` seconds and read one sample."""
        amps = self.exp.commanded_current(elapsed)
        self.instruments.write_current(amps)

        supply_v = self.instruments.read_supply_voltage()
        raw_temp = self.instruments.read_raw_temperature()
        # No current -> no meaningful voltage drop or resistance (guards the
        # original's ZeroDivisionError on the very first sample).
        measured_v = self.instruments.read_measured_voltage() if amps > 0 else 0.0
        resistance = (measured_v / amps) if amps > 0 else 0.0

        return Sample(
            time_s=elapsed,
            current_a=amps,
            current_density=amps / self.exp.area,
            voltage_measured=measured_v,
            voltage_supply=supply_v,
            resistance_ohm=resistance,
            temperature_c=self.hw.raw_to_celsius(raw_temp),
        )

    # -- blocking run -----------------------------------------------------
    def run(
        self,
        *,
        stop_event: Optional[threading.Event] = None,
        on_sample: Optional[SampleCallback] = None,
        retain_samples: bool = True,
    ) -> RunResult:
        """Run to completion (or until ``stop_event`` is set). Blocking."""
        self.validate()
        stop_event = stop_event or threading.Event()
        result = RunResult()
        total_time = self.exp.execution_time()

        writer = (
            CsvDataWriter(
                self.exp.output_dir, self.exp.file_name, pyro_min_temp=self.hw.pyro_min_temp
            )
            if self.write_file
            else None
        )

        self.instruments.open()
        try:
            self.instruments.reset_current()
            if writer is not None:
                writer.open()
            start = self._clock()
            while not stop_event.is_set():
                elapsed = self._clock() - start
                if elapsed > total_time:
                    result.completed = True
                    break
                sample = self.measure(elapsed)
                if writer is not None:
                    writer.write(sample)
                if retain_samples:
                    result.samples.append(sample)
                if on_sample is not None:
                    on_sample(sample)
                result.elapsed = elapsed
                self._sleep(self.exp.sampling_period)
        finally:
            if writer is not None:
                writer.close()
            # Always leave the hardware in a safe, idle state.
            try:
                self.instruments.reset_current()
            finally:
                self.instruments.close()

        result.stopped = stop_event.is_set()
        return result

    # -- asynchronous run -------------------------------------------------
    def start_in_thread(
        self,
        *,
        on_sample: Optional[SampleCallback] = None,
        on_finish: Optional[FinishCallback] = None,
    ) -> RunHandle:
        """Run on a daemon worker thread; returns a :class:`RunHandle`.

        Exceptions are captured into ``RunResult.error`` and delivered to
        ``on_finish`` rather than crashing the worker thread silently.
        """
        # Validate eagerly so configuration errors surface to the caller
        # synchronously instead of vanishing inside the thread.
        self.validate()
        stop_event = threading.Event()

        def _target() -> None:
            try:
                result = self.run(stop_event=stop_event, on_sample=on_sample)
            except BaseException as exc:  # noqa: BLE001 - reported, not swallowed
                result = RunResult(error=exc, stopped=stop_event.is_set())
            if on_finish is not None:
                on_finish(result)

        thread = threading.Thread(target=_target, name="flash-acquisition", daemon=True)
        thread.start()
        return RunHandle(thread=thread, stop_event=stop_event)
