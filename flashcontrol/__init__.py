"""Real-time flash experiment control, acquisition and visualization.

A flash (sintering) experiment ramps a controlled current through a sample
while measuring voltage and temperature, capturing the rapid "flash" event.
This package separates that workflow into testable layers:

* :mod:`flashcontrol.config`   - parameter dataclasses + validation
* :mod:`flashcontrol.hardware` - instrument backends (real DAQ/Keithley + simulation)
* :mod:`flashcontrol.core`     - the experiment runner and data model
* :mod:`flashcontrol.gui`      - the Tkinter front end (optional, needs matplotlib)

Only ``config``, ``hardware`` and ``core`` are needed to run a simulated
experiment or the test suite; none of them import Tk, matplotlib, nidaqmx or
pyvisa at module load time.

Originally authored by Emmanuel Bamidele (2023); released under Apache-2.0.
"""

from .config import ExperimentConfig, HardwareConfig
from .core import ExperimentRunner, Sample

__version__ = "2.0.0"

__all__ = [
    "ExperimentConfig",
    "HardwareConfig",
    "ExperimentRunner",
    "Sample",
    "__version__",
]
