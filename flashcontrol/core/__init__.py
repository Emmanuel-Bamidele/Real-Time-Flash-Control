"""Pure experiment logic: data model, runner and CSV writer.

Nothing in this package imports Tk, matplotlib, nidaqmx or pyvisa, so it is
fully unit-testable against the simulated backend (or any fake).
"""

from __future__ import annotations

from .sample import Sample
from .runner import ExperimentRunner, RunResult
from .writer import CsvDataWriter

__all__ = ["Sample", "ExperimentRunner", "RunResult", "CsvDataWriter"]
