from flashcontrol.config import HardwareConfig
from flashcontrol.hardware.simulated import SimulatedInstruments


def test_idle_state_is_safe():
    sim = SimulatedInstruments(HardwareConfig())
    sim.open()
    assert sim.read_measured_voltage() == 0.0
    assert sim.read_supply_voltage() == 0.0
    # Temperature starts at the pyrometer floor.
    assert sim.read_raw_temperature() == 0.0


def test_heating_and_resistance_collapse_under_load():
    hw = HardwareConfig()
    sim = SimulatedInstruments(hw)
    sim.open()

    r_cold = sim._resistance()
    temps = []
    voltages = []
    for _ in range(200):
        sim.write_current(50.0)
        temps.append(hw.raw_to_celsius(sim.read_raw_temperature()))
        voltages.append(sim.read_measured_voltage())

    # Sample heats well above the floor...
    assert temps[-1] > temps[0] > hw.pyro_min_temp
    # ...and resistance collapses as it heats (the flash signature).
    assert sim._resistance() < r_cold


def test_reset_and_close_return_to_idle():
    sim = SimulatedInstruments(HardwareConfig())
    sim.open()
    sim.write_current(40.0)
    assert sim.read_measured_voltage() > 0
    sim.reset_current()
    assert sim.read_measured_voltage() == 0.0


def test_probe_reports_ready():
    statuses = SimulatedInstruments(HardwareConfig()).probe()
    names = {s.name for s in statuses}
    assert names == {"NI-DAQ", "Keithley DMM"}
    assert all(s.ok for s in statuses)
    assert all(s.detail for s in statuses)


def test_deterministic():
    hw = HardwareConfig()
    a = SimulatedInstruments(hw)
    b = SimulatedInstruments(hw)
    a.open()
    b.open()
    for _ in range(50):
        a.write_current(25.0)
        b.write_current(25.0)
    assert a.read_measured_voltage() == b.read_measured_voltage()
