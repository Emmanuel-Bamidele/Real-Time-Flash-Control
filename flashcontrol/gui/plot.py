"""Embedded live plot.

Replaces the original ``plt.pause`` loop - which fought the Tk event loop - with
a :class:`~matplotlib.backends.backend_tkagg.FigureCanvasTkAgg` canvas that lives
inside the window and is refreshed from the GUI thread. The figure is styled to
match the application's theme so it reads as one premium surface.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("TkAgg")  # must precede the pyplot/backend import

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402

from ..core.sample import Sample  # noqa: E402
from .theme import PALETTE  # noqa: E402

# Selectable plot channels: label -> (Sample attribute, axis caption).
CHANNELS = {
    "Time (s)": ("time_s", "Time (s)"),
    "Voltage (V)": ("voltage_measured", "Voltage (V)"),
    "Current (A)": ("current_a", "Current (A)"),
    "Resistance (Ω)": ("resistance_ohm", "Resistance (Ω)"),
    "Current Density (A/mm2)": ("current_density", "Current Density (A/mm²)"),
    "Temperature (°C)": ("temperature_c", "Temperature (°C)"),
}

X_OPTIONS = ["Time (s)", "Temperature (°C)", "Current Density (A/mm2)"]
Y_OPTIONS = [
    "Voltage (V)",
    "Current (A)",
    "Temperature (°C)",
    "Resistance (Ω)",
    "Current Density (A/mm2)",
]


class LivePlot:
    """A dual-y-axis live plot embedded in a Tk container."""

    def __init__(self, master, palette: dict | None = None) -> None:
        self.p = palette or PALETTE
        self.figure = Figure(figsize=(6, 3.2), dpi=100, facecolor=self.p["card_bg"])
        self.ax1 = self.figure.add_subplot(111)
        self.ax2 = self.ax1.twinx()
        (self.line1,) = self.ax1.plot(
            [], [], color=self.p["plot_line1"], linewidth=2.2, solid_capstyle="round"
        )
        (self.line2,) = self.ax2.plot(
            [], [], color=self.p["plot_line2"], linewidth=2.2, solid_capstyle="round"
        )

        self.canvas = FigureCanvasTkAgg(self.figure, master=master)
        self.widget = self.canvas.get_tk_widget()
        self.widget.configure(highlightthickness=0, borderwidth=0)

        self._series = {label: [] for label in CHANNELS}
        self._x = "Time (s)"
        self._y1 = "Voltage (V)"
        self._y2 = "Current (A)"
        self._style_axes()
        self._configure_axes()

    def _style_axes(self) -> None:
        for ax in (self.ax1, self.ax2):
            ax.set_facecolor(self.p["card_bg"])
            ax.tick_params(colors=self.p["muted"], labelsize=9)
            for spine in ax.spines.values():
                spine.set_color(self.p["card_border"])
        self.ax1.grid(True, color=self.p["plot_grid"], linewidth=0.8, alpha=0.9)

    def set_axes(self, x_label: str, y1_label: str, y2_label: str) -> None:
        self._x, self._y1, self._y2 = x_label, y1_label, y2_label
        self._configure_axes()

    def _configure_axes(self) -> None:
        self.ax1.set_xlabel(CHANNELS[self._x][1], fontsize=11, color=self.p["text"])
        self.ax1.set_ylabel(CHANNELS[self._y1][1], color=self.p["plot_line1"], fontsize=11)
        self.ax1.tick_params(axis="y", labelcolor=self.p["plot_line1"])
        self.ax2.set_ylabel(CHANNELS[self._y2][1], color=self.p["plot_line2"], fontsize=11)
        self.ax2.tick_params(axis="y", labelcolor=self.p["plot_line2"])
        self.ax1.set_title(
            f"{CHANNELS[self._y1][1]} & {CHANNELS[self._y2][1]} vs {CHANNELS[self._x][1]}",
            fontsize=12,
            color=self.p["text"],
            pad=12,
            fontweight="bold",
        )
        self.figure.tight_layout()

    def reset(self) -> None:
        for series in self._series.values():
            series.clear()
        self.redraw()

    def append(self, sample: Sample) -> None:
        for label, (attr, _) in CHANNELS.items():
            self._series[label].append(getattr(sample, attr))

    def redraw(self) -> None:
        x = self._series[self._x]
        self.line1.set_data(x, self._series[self._y1])
        self.line2.set_data(x, self._series[self._y2])
        for ax in (self.ax1, self.ax2):
            ax.relim()
            ax.autoscale_view()
        self.canvas.draw_idle()
