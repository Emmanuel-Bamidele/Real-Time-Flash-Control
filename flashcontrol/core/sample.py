"""A single acquired data point."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Sample:
    """One measurement row from a flash run.

    Field order matches the CSV column order so writing stays trivial.
    """

    time_s: float
    current_a: float
    current_density: float  # A/mm^2
    voltage_measured: float  # Keithley, V
    voltage_supply: float  # power supply, V
    resistance_ohm: float
    temperature_c: float

    def as_row(self) -> list:
        """Values in CSV column order."""
        return [
            self.time_s,
            self.current_a,
            self.current_density,
            self.voltage_measured,
            self.voltage_supply,
            self.resistance_ohm,
            self.temperature_c,
        ]


# CSV header metadata, kept next to the row definition so they cannot drift.
COLUMN_NAMES = [
    "Time",
    "Current",
    "Current Density",
    "Voltage (Keithley)",
    "Voltage (Power Supply)",
    "Resistance",
    "Temperature",
]

COLUMN_UNITS = ["s", "A", "A/mm2", "V", "V", "ohms", "C"]
