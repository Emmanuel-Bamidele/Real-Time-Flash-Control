"""The Tkinter application window.

Wires the configuration dataclasses, the chosen instrument backend and the
:class:`~flashcontrol.core.runner.ExperimentRunner` to a graphical front end.

Key differences from the original single-file GUI:

* Acquisition runs on a worker thread; samples reach the GUI through a
  thread-safe queue drained via ``after()``. The window stays responsive and
  **Stop actually stops** the run.
* A "Simulate" toggle selects the driver-free backend, so the app launches and
  can be demonstrated with no DAQ/Keithley attached.
* Inputs are parsed into validated config objects up front; bad values raise a
  clear dialog instead of crashing mid-run.
* A modern, themed look (see :mod:`flashcontrol.gui.theme`) - header bar, card
  panels, accent buttons and a styled live plot.
"""

from __future__ import annotations

import queue
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from ..config import ConfigError, ExperimentConfig, HardwareConfig
from ..core.runner import ExperimentRunner, RunResult
from ..hardware import make_instruments
from .help import show_help
from .plot import LivePlot, X_OPTIONS, Y_OPTIONS
from .theme import apply_theme

# Default field values (label -> default), grouped by panel.
_HARDWARE_FIELDS = [
    ("Temp. Channel", "temperature_channel", "Dev1/ai2"),
    ("Current Channel", "current_channel", "Dev1/ao1"),
    ("Voltage Channel", "voltage_channel", "Dev1/ai0"),
    ("Keithley Address", "keithley_address", "13"),
    ("DAQ Max Volts", "daq_max_voltage", "10"),
    ("PS Max Current", "ps_max_current", "100"),
    ("PS Max Voltage", "ps_max_voltage", "30"),
    ("Pyro Min Temp", "pyro_min_temp", "650"),
    ("Temp Scale", "temp_scale", "230"),
]

_EXPERIMENT_FIELDS = [
    ("Area (mm²)", "area", "1.0"),
    ("Current Density (A/mm²)", "current_density", "1.0"),
    ("Current Rate (A/s)", "current_rate", "1.0"),
    ("Holding Time (s)", "holding_time", "0.0"),
    ("Sampling Period (s)", "sampling_period", "0.01"),
]

_READOUTS = [
    ("TIME (s)", "time_s"),
    ("CURRENT (A)", "current_a"),
    ("DENSITY (A/mm²)", "current_density"),
    ("VOLTAGE (V)", "voltage_measured"),
    ("RESISTANCE (Ω)", "resistance_ohm"),
    ("TEMP (°C)", "temperature_c"),
]


class FlashControlApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Real-Time Flash Control — Current-Controlled")
        self.root.geometry("1200x840")
        self.root.minsize(1080, 800)
        self.theme = apply_theme(root)
        self.p = self.theme.palette
        self._build_menubar()

        self.entries: dict[str, ttk.Entry] = {}
        self.readouts: dict[str, tk.StringVar] = {}
        self._output_dir = ""
        self._queue: "queue.Queue" = queue.Queue()
        self._handle = None

        self.simulate_var = tk.BooleanVar(value=True)
        self.file_name_var = tk.StringVar(value="flash_run")
        self.limit_var = tk.StringVar(value="—")
        self.status_var = tk.StringVar(value="Ready.")
        self.x_var = tk.StringVar(value="Time (s)")
        self.y1_var = tk.StringVar(value="Voltage (V)")
        self.y2_var = tk.StringVar(value="Current (A)")

        self._build_ui()

    # -- UI construction --------------------------------------------------
    def _build_ui(self) -> None:
        self._build_header()

        body = ttk.Frame(self.root, style="TFrame", padding=(14, 8))
        body.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(body, style="TFrame")
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 12))
        right = ttk.Frame(body, style="TFrame")
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self._build_card_fields(left, "Interfacing Parameters", _HARDWARE_FIELDS, columns=2)
        self._build_parameters(left)
        self._build_file_controls(left)
        self._build_run_controls(left)

        self._build_plot(right)
        self._build_readouts(right)

        ttk.Label(self.root, textvariable=self.status_var, style="Status.TLabel", anchor=tk.W).pack(
            side=tk.BOTTOM, fill=tk.X
        )

    def _build_menubar(self) -> None:
        menubar = tk.Menu(self.root)
        helpmenu = tk.Menu(menubar, tearoff=0)
        helpmenu.add_command(label="Setup & Hardware Guide", command=self._show_help)
        helpmenu.add_command(label="How to Cite", command=self._show_help)
        helpmenu.add_separator()
        helpmenu.add_command(label="About", command=self._show_help)
        menubar.add_cascade(label="Help", menu=helpmenu)
        self.root.config(menu=menubar)

    def _show_help(self) -> None:
        show_help(self.root, self.theme)

    def _build_header(self) -> None:
        header = ttk.Frame(self.root, style="Header.TFrame", padding=(18, 9))
        header.pack(side=tk.TOP, fill=tk.X)

        text = ttk.Frame(header, style="Header.TFrame")
        text.pack(side=tk.LEFT)
        title_row = ttk.Frame(text, style="Header.TFrame")
        title_row.pack(anchor=tk.W)
        ttk.Label(title_row, text="Real-Time Flash Control", style="Header.TLabel").pack(
            side=tk.LEFT
        )
        ttk.Label(title_row, text="CURRENT-CONTROLLED", style="Badge.TLabel").pack(
            side=tk.LEFT, padx=(12, 0)
        )
        ttk.Label(
            text,
            text="Current-controlled flash experiment · acquisition · live visualization",
            style="HeaderSub.TLabel",
        ).pack(anchor=tk.W, pady=(2, 0))

        # Clickable Help link on the right of the header.
        link = ttk.Label(header, text="Help  ⓘ", style="HeaderLink.TLabel", cursor="hand2")
        link.pack(side=tk.RIGHT, padx=(0, 4))
        link.bind("<Button-1>", lambda _e: self._show_help())

        # thin accent underline for a premium finish
        tk.Frame(self.root, background=self.p["accent"], height=3).pack(side=tk.TOP, fill=tk.X)

    def _card(self, parent, title) -> ttk.LabelFrame:
        frame = ttk.LabelFrame(parent, text=title, style="Card.TLabelframe")
        frame.pack(fill=tk.X, pady=4)
        return frame

    def _build_card_fields(self, parent, title, fields, columns=1) -> ttk.LabelFrame:
        frame = self._card(parent, title)
        for i, (label, key, default) in enumerate(fields):
            group = i % columns
            row = i // columns
            base = group * 2
            ttk.Label(frame, text=label, style="Field.TLabel").grid(
                row=row, column=base, sticky=tk.W, padx=(2, 6), pady=2
            )
            entry = ttk.Entry(frame, width=11)
            entry.insert(0, default)
            entry.grid(row=row, column=base + 1, sticky=tk.EW, padx=(0, 10), pady=2)
            self.entries[key] = entry
        for c in range(columns):
            frame.columnconfigure(c * 2 + 1, weight=1)
        return frame

    def _build_parameters(self, parent) -> None:
        frame = self._build_card_fields(parent, "Flash Parameters", _EXPERIMENT_FIELDS, columns=1)
        row = len(_EXPERIMENT_FIELDS)
        ttk.Label(frame, text="Current Limit (A)", style="Field.TLabel").grid(
            row=row, column=0, sticky=tk.W, padx=2, pady=(5, 2)
        )
        ttk.Label(frame, textvariable=self.limit_var, style="Limit.TLabel").grid(
            row=row, column=1, sticky=tk.E, padx=(0, 10), pady=(5, 2)
        )
        ttk.Button(
            frame, text="Update Control", style="Accent.TButton", command=self._update_limit
        ).grid(row=row + 1, column=0, columnspan=2, sticky=tk.EW, pady=(6, 2))

    def _build_file_controls(self, parent) -> None:
        frame = self._card(parent, "Output")
        ttk.Label(frame, text="File Name", style="Field.TLabel").grid(
            row=0, column=0, sticky=tk.W, padx=2, pady=2
        )
        ttk.Entry(frame, textvariable=self.file_name_var, width=18).grid(
            row=0, column=1, sticky=tk.EW, padx=(0, 10), pady=2
        )
        frame.columnconfigure(1, weight=1)
        self.folder_btn = ttk.Button(
            frame, text="Choose Folder…", command=self._choose_folder
        )
        self.folder_btn.grid(row=1, column=0, columnspan=2, sticky=tk.EW, pady=(5, 2))

    def _build_run_controls(self, parent) -> None:
        frame = ttk.Frame(parent, style="Card.TFrame", padding=8)
        frame.pack(fill=tk.X, pady=4)
        ttk.Checkbutton(
            frame, text="Simulate (no hardware)", variable=self.simulate_var
        ).pack(anchor=tk.W, pady=(0, 6))
        btns = ttk.Frame(frame, style="Card.TFrame")
        btns.pack(fill=tk.X)
        self.start_btn = ttk.Button(
            btns, text="▶  Start", style="Success.TButton", command=self._start
        )
        self.start_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 4))
        self.stop_btn = ttk.Button(
            btns, text="■  Stop", style="Danger.TButton", command=self._stop, state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(4, 0))

    def _build_plot(self, parent) -> None:
        axes = ttk.Frame(parent, style="Card.TFrame", padding=8)
        axes.pack(fill=tk.X)
        for col, (text, var, opts) in enumerate(
            [
                ("X axis", self.x_var, X_OPTIONS),
                ("Primary Y", self.y1_var, Y_OPTIONS),
                ("Secondary Y", self.y2_var, Y_OPTIONS),
            ]
        ):
            ttk.Label(axes, text=text, style="Field.TLabel").grid(
                row=0, column=col * 2, padx=(8, 4), pady=2
            )
            ttk.OptionMenu(axes, var, var.get(), *opts, command=self._on_axis_change).grid(
                row=0, column=col * 2 + 1, padx=(0, 12), pady=2
            )

        container = ttk.Frame(parent, style="Card.TFrame", padding=6)
        container.pack(fill=tk.BOTH, expand=True, pady=6)
        self.plot = LivePlot(container, palette=self.p)
        self.plot.widget.pack(fill=tk.BOTH, expand=True)

    def _build_readouts(self, parent) -> None:
        frame = ttk.Frame(parent, style="TFrame")
        frame.pack(fill=tk.X)
        for col, (label, key) in enumerate(_READOUTS):
            card = ttk.Frame(frame, style="Card.TFrame", padding=(10, 8))
            card.grid(row=0, column=col, sticky=tk.NSEW, padx=4)
            frame.columnconfigure(col, weight=1)
            var = tk.StringVar(value="0.0")
            self.readouts[key] = var
            ttk.Label(card, text=label, style="ReadoutCap.TLabel").pack(anchor=tk.W)
            ttk.Label(card, textvariable=var, style="Readout.TLabel").pack(anchor=tk.W)

    # -- actions ----------------------------------------------------------
    def _on_axis_change(self, _value=None) -> None:
        self.plot.set_axes(self.x_var.get(), self.y1_var.get(), self.y2_var.get())

    def _choose_folder(self) -> None:
        path = filedialog.askdirectory()
        if path:
            self._output_dir = path
            self.folder_btn.config(text=f"📁 {path.split('/')[-1] or path}")

    def _build_hardware(self) -> HardwareConfig:
        g = lambda k: self.entries[k].get()  # noqa: E731
        return HardwareConfig(
            temperature_channel=g("temperature_channel"),
            current_channel=g("current_channel"),
            voltage_channel=g("voltage_channel"),
            keithley_address=g("keithley_address"),
            daq_max_voltage=float(g("daq_max_voltage")),
            ps_max_current=float(g("ps_max_current")),
            ps_max_voltage=float(g("ps_max_voltage")),
            pyro_min_temp=float(g("pyro_min_temp")),
            temp_scale=float(g("temp_scale")),
        )

    def _build_experiment(self) -> ExperimentConfig:
        g = lambda k: self.entries[k].get()  # noqa: E731
        return ExperimentConfig(
            area=float(g("area")),
            current_density=float(g("current_density")),
            current_rate=float(g("current_rate")),
            holding_time=float(g("holding_time")),
            sampling_period=float(g("sampling_period")),
            output_dir=self._output_dir,
            file_name=self.file_name_var.get(),
        )

    def _update_limit(self) -> None:
        try:
            hw = self._build_hardware()
            exp = self._build_experiment()
            exp.check_against_supply(hw)
            self.limit_var.set(f"{exp.current_limit:.3f}")
            self.status_var.set("Control updated.")
        except (ConfigError, ValueError) as exc:
            self.limit_var.set("limit!")
            self.status_var.set(f"Error: {exc}")

    def _start(self) -> None:
        try:
            hw = self._build_hardware()
            exp = self._build_experiment()
            instruments = make_instruments(hw, simulate=self.simulate_var.get())
            runner = ExperimentRunner(exp, hw, instruments)
            self._handle = runner.start_in_thread(
                on_sample=self._queue.put, on_finish=self._on_finish
            )
        except (ConfigError, ValueError) as exc:
            messagebox.showerror("Cannot start", str(exc))
            return
        except Exception as exc:  # hardware open failures, etc.
            messagebox.showerror("Cannot start", f"{type(exc).__name__}: {exc}")
            return

        self.limit_var.set(f"{exp.current_limit:.3f}")
        self.plot.set_axes(self.x_var.get(), self.y1_var.get(), self.y2_var.get())
        self.plot.reset()
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_var.set("Running…")
        self.root.after(50, self._drain_queue)

    def _stop(self) -> None:
        if self._handle is not None:
            self._handle.stop()
            self.status_var.set("Stopping…")

    def _drain_queue(self) -> None:
        finished: "RunResult | None" = None
        try:
            while True:
                item = self._queue.get_nowait()
                if isinstance(item, tuple) and item and item[0] == "finish":
                    finished = item[1]
                    break
                self.plot.append(item)
                self._update_readouts(item)
        except queue.Empty:
            pass

        self.plot.redraw()
        if finished is not None:
            self._handle_finish(finished)
        else:
            self.root.after(50, self._drain_queue)

    def _update_readouts(self, sample) -> None:
        for key, var in self.readouts.items():
            var.set(f"{getattr(sample, key):.4g}")

    def _on_finish(self, result: RunResult) -> None:
        # Runs on the worker thread - hand off to the GUI thread via the queue.
        self._queue.put(("finish", result))

    def _handle_finish(self, result: RunResult) -> None:
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self._handle = None
        if result.error is not None:
            self.status_var.set(f"Error: {result.error}")
            messagebox.showerror("Run failed", f"{type(result.error).__name__}: {result.error}")
        elif result.stopped:
            self.status_var.set(f"Stopped after {len(result.samples)} samples.")
        else:
            self.status_var.set(f"Done. {len(result.samples)} samples acquired.")
            messagebox.showinfo("Done", "Acquisition finished!")


def run() -> None:
    root = tk.Tk()
    FlashControlApp(root)
    root.mainloop()
