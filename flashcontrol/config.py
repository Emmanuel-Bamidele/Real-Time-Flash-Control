"""Configuration dataclasses for a flash experiment.

Two immutable-ish value objects replace the dozens of module-level globals and
GUI-field-as-state-store reads in the original script:

* :class:`HardwareConfig` - how to talk to the instruments (channels, scales).
* :class:`ExperimentConfig` - what experiment to run (ramp, area, timing).

Both validate themselves and expose the derived quantities (current/voltage
scales, current limit, execution time) that the runner and hardware need, so
the maths lives in exactly one place.
"""

from __future__ import annotations

from dataclasses import dataclass


class ConfigError(ValueError):
    """Raised when a configuration value is missing or out of range."""


@dataclass
class HardwareConfig:
    """Instrument wiring and full-scale ranges.

    The DAQ commands current via an analog-output voltage and reads the supply
    voltage / temperature via analog inputs. ``*_scale`` convert between the
    physical quantity and the 0..``daq_max_voltage`` signal, exactly as the
    original software did::

        commanded_ao_volts = amps / current_scale
        supply_volts       = raw_ai_volts * voltage_scale
    """

    temperature_channel: str = "Dev1/ai2"
    current_channel: str = "Dev1/ao1"
    voltage_channel: str = "Dev1/ai0"
    keithley_address: str = "13"

    daq_max_voltage: float = 10.0
    ps_max_current: float = 100.0
    ps_max_voltage: float = 30.0

    # Pyrometer: celsius = raw_reading * temp_scale + pyro_min_temp.
    # In the original these were the magic numbers 230 and 650.
    pyro_min_temp: float = 650.0
    temp_scale: float = 230.0

    def validate(self) -> None:
        if self.daq_max_voltage <= 0:
            raise ConfigError("DAQ max voltage must be positive.")
        if self.ps_max_current <= 0:
            raise ConfigError("Power-supply max current must be positive.")
        if self.ps_max_voltage <= 0:
            raise ConfigError("Power-supply max voltage must be positive.")
        for name in ("temperature_channel", "current_channel", "voltage_channel"):
            if not getattr(self, name).strip():
                raise ConfigError(f"{name.replace('_', ' ')} must not be empty.")

    @property
    def current_scale(self) -> float:
        """Amps per volt of analog-output command."""
        return self.ps_max_current / self.daq_max_voltage

    @property
    def voltage_scale(self) -> float:
        """Volts (supply) per volt of analog-input reading."""
        return self.ps_max_voltage / self.daq_max_voltage

    def raw_to_celsius(self, raw: float) -> float:
        """Convert a raw pyrometer DAQ reading to degrees Celsius."""
        return raw * self.temp_scale + self.pyro_min_temp


@dataclass
class ExperimentConfig:
    """The experiment recipe and where to store its data."""

    area: float = 1.0  # sample cross-section, mm^2
    current_density: float = 1.0  # target density, A/mm^2
    current_rate: float = 1.0  # ramp rate, A/s
    holding_time: float = 0.0  # dwell at the limit, s
    sampling_period: float = 0.01  # delay between samples, s

    output_dir: str = ""
    file_name: str = "flash_run"

    def validate(self) -> None:
        if self.area <= 0:
            raise ConfigError("Sample area must be positive.")
        if self.current_density <= 0:
            raise ConfigError("Current density must be positive.")
        if self.current_rate <= 0:
            raise ConfigError("Current rate must be positive (it sets the ramp).")
        if self.holding_time < 0:
            raise ConfigError("Holding time cannot be negative.")
        if self.sampling_period <= 0:
            raise ConfigError("Sampling period must be positive.")
        if not self.file_name.strip():
            raise ConfigError("File name must not be empty.")

    @property
    def current_limit(self) -> float:
        """Peak current the ramp targets, in amps (density x area)."""
        return self.current_density * self.area

    def check_against_supply(self, hardware: HardwareConfig) -> None:
        """Ensure the requested current limit fits the power supply."""
        if self.current_limit > hardware.ps_max_current:
            raise ConfigError(
                f"Current limit {self.current_limit:.3f} A exceeds the supply "
                f"maximum of {hardware.ps_max_current:.3f} A."
            )

    def execution_time(self) -> float:
        """Total run length: ramp time to the limit plus the hold."""
        return self.current_limit / self.current_rate + self.holding_time

    def commanded_current(self, elapsed: float) -> float:
        """Current setpoint at ``elapsed`` seconds, clamped to the limit."""
        return min(self.current_rate * elapsed, self.current_limit)
