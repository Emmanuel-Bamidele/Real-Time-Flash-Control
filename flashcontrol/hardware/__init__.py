"""Instrument backends for the flash experiment.

All backends implement the :class:`~flashcontrol.hardware.base.Instruments`
interface so the runner is agnostic to whether it is driving real hardware or
a simulation. The concrete classes are imported lazily by :func:`make_instruments`
so that importing this package never requires ``nidaqmx``/``pyvisa`` (real) or
forces a particular backend.
"""

from __future__ import annotations

from .base import Instruments

__all__ = ["Instruments", "make_instruments"]


def make_instruments(hardware, *, simulate: bool) -> Instruments:
    """Return a ready-to-open backend for ``hardware``.

    ``simulate=True`` yields the in-process :class:`SimulatedInstruments`, which
    needs no drivers. ``simulate=False`` yields the real DAQ/Keithley backend,
    importing ``nidaqmx``/``pyvisa`` only at that point.
    """
    if simulate:
        from .simulated import SimulatedInstruments

        return SimulatedInstruments(hardware)

    from .nidaq import NiDaqInstruments

    return NiDaqInstruments(hardware)
