"""Tab-separated data file writer.

Preserves the original file format (tab-separated ``.csv`` with a name row, a
unit row, and a zeroed first sample) while fixing the cross-platform path bug -
paths are joined with :func:`os.path.join`, not a hard-coded ``\\``.

Usable as a context manager so the file is always flushed and closed, even if
the run aborts::

    with CsvDataWriter(directory, "run", pyro_min_temp=650) as writer:
        writer.write(sample)
"""

from __future__ import annotations

import os
from typing import Optional

from .sample import COLUMN_NAMES, COLUMN_UNITS, Sample


class CsvDataWriter:
    """Append :class:`Sample` rows to a tab-separated file."""

    def __init__(self, directory: str, file_name: str, *, pyro_min_temp: float) -> None:
        if not directory:
            raise ValueError("Output directory must be selected before a run.")
        if not file_name.strip():
            raise ValueError("File name must not be empty.")
        name = file_name if file_name.endswith(".csv") else f"{file_name}.csv"
        self.path = os.path.join(directory, name)
        self._pyro_min_temp = pyro_min_temp
        self._fh: Optional["object"] = None

    def open(self) -> "CsvDataWriter":
        self._fh = open(self.path, "w", encoding="utf-8")
        self._fh.write("\t".join(COLUMN_NAMES) + "\n")
        self._fh.write("\t".join(COLUMN_UNITS) + "\n")
        # Zeroed initial row at the pyrometer floor temperature.
        self._fh.write("0\t0\t0\t0\t0\t0\t" + f"{self._pyro_min_temp}\n")
        return self

    def write(self, sample: Sample) -> None:
        if self._fh is None:
            raise RuntimeError("Writer is not open; call open() first.")
        self._fh.write("\t".join(str(v) for v in sample.as_row()) + "\n")

    def close(self) -> None:
        if self._fh is not None:
            self._fh.close()
            self._fh = None

    def __enter__(self) -> "CsvDataWriter":
        return self.open()

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()
