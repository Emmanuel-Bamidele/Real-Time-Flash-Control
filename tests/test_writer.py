import os

import pytest

from flashcontrol.core.sample import Sample
from flashcontrol.core.writer import CsvDataWriter


def test_writer_uses_os_path_join(tmp_path):
    # Regression: the original hard-coded a Windows "\\" separator.
    writer = CsvDataWriter(str(tmp_path), "myrun", pyro_min_temp=650)
    assert writer.path == os.path.join(str(tmp_path), "myrun.csv")


def test_writer_emits_header_units_and_rows(tmp_path):
    sample = Sample(
        time_s=0.5,
        current_a=1.0,
        current_density=1.0,
        voltage_measured=2.0,
        voltage_supply=2.1,
        resistance_ohm=2.0,
        temperature_c=700.0,
    )
    with CsvDataWriter(str(tmp_path), "run", pyro_min_temp=650) as writer:
        writer.write(sample)

    lines = (tmp_path / "run.csv").read_text().splitlines()
    assert lines[0].startswith("Time\t")
    assert lines[1].split("\t") == ["s", "A", "A/mm2", "V", "V", "ohms", "C"]
    assert lines[2].startswith("0\t0\t0\t0\t0\t0\t650")
    assert lines[3].split("\t")[0] == "0.5"


def test_writer_requires_directory():
    with pytest.raises(ValueError):
        CsvDataWriter("", "run", pyro_min_temp=650)


def test_write_before_open_raises(tmp_path):
    writer = CsvDataWriter(str(tmp_path), "run", pyro_min_temp=650)
    sample = Sample(0, 0, 0, 0, 0, 0, 650)
    with pytest.raises(RuntimeError):
        writer.write(sample)
