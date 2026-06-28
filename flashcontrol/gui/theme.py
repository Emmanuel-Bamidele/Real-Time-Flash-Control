"""Visual theme: a modern, premium light palette with an indigo accent.

Centralises every colour, font and ttk style so the window and the embedded
matplotlib figure share one cohesive look. Call :func:`apply_theme` once on the
root window; it returns a :class:`Theme` carrying the palette and resolved fonts
for the rest of the GUI to use.
"""

from __future__ import annotations

from dataclasses import dataclass
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

# -- palette --------------------------------------------------------------
PALETTE = {
    "app_bg": "#EEF1F6",      # window background
    "header_bg": "#1E293B",   # dark slate header bar
    "header_fg": "#F8FAFC",
    "header_sub": "#94A3B8",
    "header_chip": "#2B3B54",  # subtle chip behind the connection indicators
    "card_bg": "#FFFFFF",      # panels / cards
    "card_border": "#E2E8F0",
    "text": "#1F2933",
    "muted": "#64748B",
    "field_bg": "#F8FAFC",
    "field_border": "#CBD5E1",
    "accent": "#4F46E5",       # indigo (primary)
    "accent_hover": "#4338CA",
    "accent_active": "#3730A3",
    "success": "#059669",      # emerald (Start)
    "success_hover": "#047857",
    "danger": "#DC2626",       # red (Stop)
    "danger_hover": "#B91C1C",
    "ok_bright": "#22C55E",    # brighter dot for the dark header
    "bad_bright": "#F87171",
    "disabled": "#CBD5E1",
    "disabled_fg": "#94A3B8",
    "plot_line1": "#4F46E5",
    "plot_line2": "#DC2626",
    "plot_grid": "#E2E8F0",
    "status_bg": "#E2E8F0",
}

_FONT_PREFERENCES = [
    "Inter",
    "SF Pro Text",
    "Segoe UI",
    "Helvetica Neue",
    "Roboto",
    "DejaVu Sans",
    "Helvetica",
]


@dataclass
class Theme:
    palette: dict
    title: tkfont.Font
    subtitle: tkfont.Font
    heading: tkfont.Font
    body: tkfont.Font
    label: tkfont.Font
    button: tkfont.Font
    readout: tkfont.Font
    readout_label: tkfont.Font

    def color(self, key: str) -> str:
        return self.palette[key]


def _pick_family(root: tk.Misc) -> str:
    try:
        available = set(tkfont.families(root))
    except tk.TclError:
        return "Helvetica"
    for family in _FONT_PREFERENCES:
        if family in available:
            return family
    return "Helvetica"


def apply_theme(root: tk.Tk) -> Theme:
    family = _pick_family(root)
    theme = Theme(
        palette=PALETTE,
        title=tkfont.Font(family=family, size=17, weight="bold"),
        subtitle=tkfont.Font(family=family, size=10),
        heading=tkfont.Font(family=family, size=10, weight="bold"),
        body=tkfont.Font(family=family, size=10),
        label=tkfont.Font(family=family, size=9),
        button=tkfont.Font(family=family, size=10, weight="bold"),
        readout=tkfont.Font(family=family, size=14, weight="bold"),
        readout_label=tkfont.Font(family=family, size=8),
    )
    p = PALETTE

    root.configure(background=p["app_bg"])
    style = ttk.Style(root)
    style.theme_use("clam")  # 'clam' honours custom colours

    # Frames / containers
    style.configure("TFrame", background=p["app_bg"])
    style.configure("Card.TFrame", background=p["card_bg"])
    style.configure("Header.TFrame", background=p["header_bg"])

    # Cards (titled panels)
    style.configure(
        "Card.TLabelframe",
        background=p["card_bg"],
        bordercolor=p["card_border"],
        relief="solid",
        borderwidth=1,
        padding=8,
    )
    style.configure(
        "Card.TLabelframe.Label",
        background=p["card_bg"],
        foreground=p["accent"],
        font=theme.heading,
    )

    # Labels
    style.configure("TLabel", background=p["card_bg"], foreground=p["text"], font=theme.label)
    style.configure("Field.TLabel", background=p["card_bg"], foreground=p["muted"], font=theme.label)
    style.configure(
        "Header.TLabel", background=p["header_bg"], foreground=p["header_fg"], font=theme.title
    )
    style.configure(
        "HeaderSub.TLabel",
        background=p["header_bg"],
        foreground=p["header_sub"],
        font=theme.subtitle,
    )
    style.configure(
        "Readout.TLabel", background=p["card_bg"], foreground=p["accent"], font=theme.readout
    )
    style.configure(
        "ReadoutCap.TLabel", background=p["card_bg"], foreground=p["muted"], font=theme.readout_label
    )
    style.configure("Limit.TLabel", background=p["card_bg"], foreground=p["danger"], font=theme.heading)

    # Entries
    style.configure(
        "TEntry",
        fieldbackground=p["field_bg"],
        background=p["field_bg"],
        foreground=p["text"],
        bordercolor=p["field_border"],
        lightcolor=p["field_border"],
        darkcolor=p["field_border"],
        insertcolor=p["text"],
        padding=3,
    )
    style.map("TEntry", bordercolor=[("focus", p["accent"])])

    # Checkbutton
    style.configure(
        "TCheckbutton", background=p["card_bg"], foreground=p["text"], font=theme.label
    )
    style.map("TCheckbutton", background=[("active", p["card_bg"])])

    # Option menus
    style.configure(
        "TMenubutton",
        background=p["field_bg"],
        foreground=p["text"],
        font=theme.label,
        padding=4,
        relief="flat",
    )
    style.map("TMenubutton", background=[("active", p["card_border"])])

    # Buttons -- a base plus accent / success / danger variants
    def _button(name, bg, hover, active, fg="#FFFFFF"):
        style.configure(
            name,
            background=bg,
            foreground=fg,
            font=theme.button,
            borderwidth=0,
            focusthickness=0,
            relief="flat",
            padding=(12, 8),
        )
        style.map(
            name,
            background=[("disabled", p["disabled"]), ("pressed", active), ("active", hover)],
            foreground=[("disabled", p["disabled_fg"])],
        )

    _button("TButton", p["card_bg"], p["card_border"], p["card_border"], fg=p["text"])
    style.map(
        "TButton",
        background=[("disabled", p["disabled"]), ("active", p["card_border"])],
        foreground=[("disabled", p["disabled_fg"])],
    )
    _button("Accent.TButton", p["accent"], p["accent_hover"], p["accent_active"])
    _button("Success.TButton", p["success"], p["success_hover"], p["success_hover"])
    _button("Danger.TButton", p["danger"], p["danger_hover"], p["danger_hover"])

    # Status bar
    style.configure(
        "Status.TLabel",
        background=p["status_bg"],
        foreground=p["muted"],
        font=theme.label,
        padding=6,
    )

    # Header "Help" link
    style.configure(
        "HeaderLink.TLabel",
        background=p["header_bg"],
        foreground=p["header_fg"],
        font=theme.heading,
    )

    # Current-controlled badge in the header
    style.configure(
        "Badge.TLabel",
        background=p["accent"],
        foreground="#FFFFFF",
        font=theme.label,
        padding=(8, 3),
    )

    # Hardware-status detail text
    style.configure(
        "StatusName.TLabel", background=p["card_bg"], foreground=p["text"], font=theme.heading
    )
    style.configure(
        "StatusDetail.TLabel", background=p["card_bg"], foreground=p["muted"], font=theme.readout_label
    )

    # Notebook (Help tabs)
    style.configure("TNotebook", background=p["app_bg"], borderwidth=0, tabmargins=(4, 4, 4, 0))
    style.configure(
        "TNotebook.Tab",
        background=p["status_bg"],
        foreground=p["muted"],
        font=theme.heading,
        padding=(14, 7),
        borderwidth=0,
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", p["card_bg"])],
        foreground=[("selected", p["accent"])],
    )

    return theme
