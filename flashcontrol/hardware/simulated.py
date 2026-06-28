"""In-process simulation backend.

Implements :class:`~flashcontrol.hardware.base.Instruments` with a small lumped
thermal/electrical model so the application can launch and the test suite can
run with no DAQ, no Keithley and no drivers installed.

The model is deliberately simple but qualitatively faithful to a flash event:

* The sample heats roughly in proportion to the current passing through it and
  cools towards the pyrometer floor temperature (Newtonian cooling).
* Its resistance *falls* as it heats (NTC / semiconducting behaviour). Because
  ``V = I * R`` and ``R`` collapses, the measured voltage rolls over even as the
  current keeps climbing - the characteristic flash signature.

It is fully deterministic (no randomness) so tests are reproducible.
"""

from __future__ import annotations

import math

from typing import List

from ..config import HardwareConfig
from .base import Instruments, InstrumentStatus

# Model constants (tuned for plausible, not physically exact, behaviour).
_HEATING_RATE = 1.5  # degC per second per amp of drive
_COOLING_RATE = 0.05  # 1/s Newtonian cooling coefficient
_R_FLOOR_OHMS = 5.0  # sample resistance at the floor temperature
_R_BETA = 0.004  # 1/degC resistance decay (drives the flash collapse)
_LEAD_OHMS = 0.1  # series lead resistance the supply also drives


class SimulatedInstruments(Instruments):
    """A driver-free flash experiment for development and testing."""

    def __init__(self, hardware: HardwareConfig, *, dt: float = 0.05) -> None:
        self.hw = hardware
        self._dt = dt
        self._opened = False
        self._reset_state()

    def _reset_state(self) -> None:
        self._current = 0.0
        self._temp_c = self.hw.pyro_min_temp
        self._step = 0

    # -- lifecycle --------------------------------------------------------
    def open(self) -> None:
        self._opened = True
        self._reset_state()

    def close(self) -> None:
        self._current = 0.0
        self._opened = False

    # -- model ------------------------------------------------------------
    def _resistance(self) -> float:
        rise = self._temp_c - self.hw.pyro_min_temp
        return max(_R_FLOOR_OHMS * math.exp(-_R_BETA * rise), 0.05)

    def _advance(self) -> None:
        """Integrate the thermal model one ``dt`` step under the present drive."""
        gain = _HEATING_RATE * self._current
        cooling = _COOLING_RATE * (self._temp_c - self.hw.pyro_min_temp)
        self._temp_c += (gain - cooling) * self._dt
        self._temp_c = max(self._temp_c, self.hw.pyro_min_temp)
        self._step += 1

    # -- Instruments interface -------------------------------------------
    def write_current(self, amps: float) -> None:
        self._current = max(0.0, amps)
        self._advance()

    def reset_current(self) -> None:
        self._current = 0.0

    def read_supply_voltage(self) -> float:
        return self._current * (self._resistance() + _LEAD_OHMS)

    def read_measured_voltage(self) -> float:
        return self._current * self._resistance()

    def read_raw_temperature(self) -> float:
        # Inverse of HardwareConfig.raw_to_celsius so the runner recovers the
        # true temperature through the normal conversion path.
        return (self._temp_c - self.hw.pyro_min_temp) / self.hw.temp_scale

    def probe(self) -> List[InstrumentStatus]:
        # The simulator is always ready - no hardware to find.
        return [
            InstrumentStatus("NI-DAQ", True, "Simulated device — ready"),
            InstrumentStatus("Keithley DMM", True, "Simulated instrument — ready"),
        ]
