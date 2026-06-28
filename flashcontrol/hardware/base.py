"""The instrument interface every backend implements.

Keeping this abstract is what lets the experiment runner be unit-tested with a
simulation (or a hand-written fake) instead of the physical DAQ + Keithley rig.

The contract intentionally returns *raw* sensor values where a conversion needs
experiment context (e.g. temperature), leaving that maths to
:class:`~flashcontrol.config.HardwareConfig`/the runner so it lives in one place
and stays testable.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class Instruments(ABC):
    """Hardware-agnostic control + measurement surface for a flash run."""

    @abstractmethod
    def open(self) -> None:
        """Acquire device handles / sessions. Call before any read or write."""

    @abstractmethod
    def close(self) -> None:
        """Release device handles. Safe to call even if :meth:`open` failed."""

    @abstractmethod
    def write_current(self, amps: float) -> None:
        """Command the supply to source ``amps`` amperes."""

    @abstractmethod
    def reset_current(self) -> None:
        """Drive the commanded current to zero (safe idle state)."""

    @abstractmethod
    def read_supply_voltage(self) -> float:
        """Read the power-supply output voltage, in volts."""

    @abstractmethod
    def read_measured_voltage(self) -> float:
        """Read the precise sample voltage (Keithley), in volts."""

    @abstractmethod
    def read_raw_temperature(self) -> float:
        """Read the raw pyrometer signal (convert via ``HardwareConfig``)."""

    # -- convenience: usable as a context manager -------------------------
    def __enter__(self) -> "Instruments":
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()
