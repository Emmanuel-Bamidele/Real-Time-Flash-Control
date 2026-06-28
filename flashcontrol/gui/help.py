"""In-app Help: setup guide, hardware requirements, and citation.

Opened from the header "Help" link and the Help menu. Presented as a themed,
tabbed window so users can find setup steps, the equipment list and the
citation without leaving the application.
"""

from __future__ import annotations

import tkinter as tk
import webbrowser
from tkinter import ttk

from .. import __version__

REPO_URL = "https://github.com/Emmanuel-Bamidele/Real-Time-Flash-Control"
DOI_URL = "https://doi.org/10.6084/m9.figshare.24054759.v1"
WEBSITE_URL = "https://www.emmanuelbamidele.com"
CONTACT_EMAIL = "correspondence.bamidele@gmail.com"

SETUP_TEXT = """\
QUICK START

This application runs a CURRENT-CONTROLLED flash (sintering) experiment: it
ramps a controlled current through the sample at a set rate up to a target
current limit, holds it, and records voltage, resistance and temperature.

1. Install
   • Python 3.9+.
   • GUI only (with the built-in simulator):
        pip install -e ".[gui,dev]"
   • Driving real hardware as well:
        pip install -e ".[gui,hardware]"

2. Launch
        python main.py
   or   python -m flashcontrol

3. Try it with no hardware
   Leave the "Simulate (no hardware)" box ticked to run a realistic simulated
   experiment - useful for learning the workflow and verifying the install.

4. Configure an experiment
   • Interfacing Parameters: DAQ channels, Keithley address and the power
     supply / DAQ full-scale ranges.
   • Flash Parameters: sample area, target current density, current rate,
     holding time and sampling period.
   • Press "Update Control" to compute the current limit (density x area) and
     check it against the supply maximum.

5. Choose an output folder and file name (data is saved as a tab-separated
   .csv), then press Start. Stop ends the run safely and resets the current.
"""

HARDWARE_TEXT = """\
EQUIPMENT & HARDWARE

The experiment is current-controlled: the DAQ commands the supply current via
an analog-output voltage, while voltage and temperature are measured back.

Required instruments
   • National Instruments DAQ device (e.g. "Dev1") providing:
        - Analog OUTPUT  -> current command       (default Dev1/ao1)
        - Analog INPUT   -> supply voltage sense  (default Dev1/ai0)
        - Analog INPUT   -> pyrometer temperature (default Dev1/ai2)
   • Programmable DC power supply operated as a current source, driven by the
     DAQ analog-output (0..DAQ Max Volts maps to 0..PS Max Current).
   • Keithley digital multimeter on GPIB (default GPIB0::13) for the precise
     sample voltage measurement.
   • Pyrometer for non-contact sample temperature.
   • The sample fixture / furnace for your flash setup.

Scaling (set under Interfacing Parameters)
   • current_scale  = PS Max Current / DAQ Max Volts
   • voltage_scale  = PS Max Voltage / DAQ Max Volts
   • Temperature (C) = raw_reading * Temp Scale + Pyro Min Temp

Software drivers
   • NI-DAQmx driver + the "nidaqmx" Python package.
   • NI-VISA + the "pyvisa" package (for GPIB / the Keithley).
   • matplotlib for the live plot.

Tip: verify channel names and the Keithley GPIB address in NI MAX before a run.
Always confirm the computed Current Limit is within your power supply's rating.
"""

CITATION_TEXT = """\
HOW TO CITE

If you publish work that used this software, please cite it:

   Bamidele, Emmanuel (2023). Real-Time Flash Experiment Control and
   Visualization software. figshare. Software.
   https://doi.org/10.6084/m9.figshare.24054759.v1

Use the "Open DOI" button below for the citable record, or "Open Repository"
for the source and documentation.

A citation is appreciated - it helps the author track where the tool is used
and prioritise enhancements.
"""

ABOUT_TEXT = """\
ABOUT

Real-Time Flash Control - current-controlled flash experiment control,
data acquisition and live visualization.

   Version : {version}
   Author  : Emmanuel Bamidele
   License : Apache License 2.0
   Contact : {email}

The software is provided for research and educational use, "as is" without
warranty of any kind. See the LICENSE file for full terms.
""".format(version=__version__, email=CONTACT_EMAIL)


def _make_tab(notebook: ttk.Notebook, theme, text: str) -> ttk.Frame:
    p = theme.palette
    frame = ttk.Frame(notebook, style="Card.TFrame", padding=2)
    widget = tk.Text(
        frame,
        wrap="word",
        background=p["card_bg"],
        foreground=p["text"],
        relief="flat",
        padx=16,
        pady=14,
        font=theme.body,
        borderwidth=0,
        highlightthickness=0,
    )
    widget.insert("1.0", text)
    widget.configure(state="disabled")
    scroll = ttk.Scrollbar(frame, orient="vertical", command=widget.yview)
    widget.configure(yscrollcommand=scroll.set)
    widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scroll.pack(side=tk.RIGHT, fill=tk.Y)
    return frame


def show_help(root: tk.Tk, theme) -> None:
    p = theme.palette
    win = tk.Toplevel(root)
    win.title("Help — Real-Time Flash Control")
    win.geometry("680x560")
    win.configure(background=p["app_bg"])
    win.transient(root)

    header = ttk.Frame(win, style="Header.TFrame", padding=(16, 10))
    header.pack(fill=tk.X)
    ttk.Label(header, text="Help & Documentation", style="Header.TLabel").pack(anchor=tk.W)
    ttk.Label(
        header,
        text="Setup · hardware · citation",
        style="HeaderSub.TLabel",
    ).pack(anchor=tk.W)
    tk.Frame(win, background=p["accent"], height=3).pack(fill=tk.X)

    notebook = ttk.Notebook(win)
    notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    for title, body in [
        ("Setup", SETUP_TEXT),
        ("Hardware", HARDWARE_TEXT),
        ("Citation", CITATION_TEXT),
        ("About", ABOUT_TEXT),
    ]:
        notebook.add(_make_tab(notebook, theme, body), text=title)

    links = ttk.Frame(win, style="Card.TFrame", padding=8)
    links.pack(fill=tk.X, padx=10, pady=(0, 10))
    ttk.Button(
        links, text="Open Repository", style="Accent.TButton",
        command=lambda: webbrowser.open_new_tab(REPO_URL),
    ).pack(side=tk.LEFT, padx=4)
    ttk.Button(
        links, text="Open DOI (cite)", style="Accent.TButton",
        command=lambda: webbrowser.open_new_tab(DOI_URL),
    ).pack(side=tk.LEFT, padx=4)
    ttk.Button(
        links, text="Website", command=lambda: webbrowser.open_new_tab(WEBSITE_URL)
    ).pack(side=tk.LEFT, padx=4)
    ttk.Button(links, text="Close", command=win.destroy).pack(side=tk.RIGHT, padx=4)

    win.lift()
    win.focus_force()
