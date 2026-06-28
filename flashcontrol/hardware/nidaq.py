"""Real instrument backend: National Instruments DAQ + Keithley over GPIB.

This is the only module that imports ``nidaqmx`` and ``pyvisa``; the imports
are deferred to construction time so the rest of the package stays importable
on machines without the drivers.

Behaviour mirrors the original script: a fresh :class:`nidaqmx.Task` is opened
for each analog read/write (cheap and robust against stuck tasks), while the
Keithley VISA session is held open for the duration of the run.
"""

from __future__ import annotations

from ..config import HardwareConfig
from .base import Instruments


class NiDaqInstruments(Instruments):
    """Drive a flash experiment with NI-DAQmx analog I/O and a Keithley DMM."""

    def __init__(self, hardware: HardwareConfig) -> None:
        self.hw = hardware
        self._multimeter = None
        # Imported here (not at module top) so importing the package does not
        # require the hardware drivers to be installed.
        import nidaqmx  # noqa: F401  (validated early; used in methods)
        import pyvisa  # noqa: F401

        self._nidaqmx = nidaqmx
        self._pyvisa = pyvisa

    # -- lifecycle --------------------------------------------------------
    def open(self) -> None:
        address = f"GPIB0::{self.hw.keithley_address}::INSTR"
        self._multimeter = self._pyvisa.ResourceManager().open_resource(address)
        self._multimeter.write(":ROUTe:CLOSe (@101)")
        self._multimeter.write(":SENSE:FUNCtion 'VOLTage'")
        self.reset_current()

    def close(self) -> None:
        try:
            self.reset_current()
        finally:
            if self._multimeter is not None:
                self._multimeter.close()
                self._multimeter = None

    # -- analog output (current command) ----------------------------------
    def _write_ao_volts(self, volts: float) -> None:
        with self._nidaqmx.Task() as task:
            task.ao_channels.add_ao_voltage_chan(
                self.hw.current_channel,
                "current_cmd",
                min_val=0,
                max_val=self.hw.daq_max_voltage,
            )
            task.start()
            task.write(volts)

    def write_current(self, amps: float) -> None:
        self._write_ao_volts(amps / self.hw.current_scale)

    def reset_current(self) -> None:
        self._write_ao_volts(0.0)

    # -- analog input (measurements) --------------------------------------
    def _read_ai_volts(self, channel: str) -> float:
        with self._nidaqmx.Task() as task:
            task.ai_channels.add_ai_voltage_chan(
                channel, min_val=0, max_val=self.hw.daq_max_voltage
            )
            task.start()
            return float(task.read())

    def read_supply_voltage(self) -> float:
        return self._read_ai_volts(self.hw.voltage_channel) * self.hw.voltage_scale

    def read_raw_temperature(self) -> float:
        return self._read_ai_volts(self.hw.temperature_channel)

    def read_measured_voltage(self) -> float:
        if self._multimeter is None:
            raise RuntimeError("Keithley session is not open; call open() first.")
        return abs(float(self._multimeter.query(":SENSE:DATA:FRESh?")))
