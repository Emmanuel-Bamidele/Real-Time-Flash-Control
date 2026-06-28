import pytest

from flashcontrol.config import ConfigError, ExperimentConfig, HardwareConfig


def test_hardware_scales():
    hw = HardwareConfig(daq_max_voltage=10, ps_max_current=100, ps_max_voltage=30)
    assert hw.current_scale == pytest.approx(10.0)  # 100 A / 10 V
    assert hw.voltage_scale == pytest.approx(3.0)  # 30 V / 10 V


def test_raw_to_celsius_uses_named_constants():
    hw = HardwareConfig(pyro_min_temp=650, temp_scale=230)
    assert hw.raw_to_celsius(0.0) == pytest.approx(650)
    assert hw.raw_to_celsius(1.0) == pytest.approx(880)


def test_current_limit_and_execution_time():
    exp = ExperimentConfig(area=2.0, current_density=10.0, current_rate=5.0, holding_time=3.0)
    assert exp.current_limit == pytest.approx(20.0)  # 10 * 2
    # ramp 20 A / 5 A/s = 4 s, + 3 s hold
    assert exp.execution_time() == pytest.approx(7.0)


def test_commanded_current_clamps_to_limit():
    exp = ExperimentConfig(area=1.0, current_density=10.0, current_rate=5.0)
    assert exp.commanded_current(0.0) == 0.0
    assert exp.commanded_current(1.0) == pytest.approx(5.0)
    assert exp.commanded_current(100.0) == pytest.approx(10.0)  # clamped to limit


def test_check_against_supply_rejects_overcurrent():
    hw = HardwareConfig(ps_max_current=10)
    exp = ExperimentConfig(area=1.0, current_density=50.0, current_rate=1.0)
    with pytest.raises(ConfigError):
        exp.check_against_supply(hw)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"area": 0},
        {"current_density": -1},
        {"current_rate": 0},
        {"holding_time": -1},
        {"sampling_period": 0},
        {"file_name": "  "},
    ],
)
def test_experiment_validation_rejects_bad_values(kwargs):
    exp = ExperimentConfig(**kwargs)
    with pytest.raises(ConfigError):
        exp.validate()
