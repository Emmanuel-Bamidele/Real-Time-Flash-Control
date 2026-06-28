"""Tkinter front end.

Importing this subpackage does not pull in Tk or matplotlib; do that through
:func:`flashcontrol.gui.app.run`, which imports them lazily so the rest of the
package stays usable in headless / test environments.
"""

from __future__ import annotations

__all__ = ["run"]


def run() -> None:
    """Launch the GUI (imports Tk + matplotlib on demand)."""
    from .app import run as _run

    _run()
