from __future__ import annotations

import tkinter as tk
from tkinter import ttk


# WatchDog desktop brand tokens.
VOID = "#0A0A0A"
ABYSS = "#0D0D0D"
DEPTH = "#141414"
SLATE = "#1E1E1E"

GUNMETAL = "#8A8A8A"
ASH = "#A3A3A3"
FROST = "#F5F5F5"

EMERALD = "#10B981"
CAUTION = "#F59E0B"
THREAT = "#EF4444"
PULSE = "#2D7EFF"

FONT_FAMILY = "Segoe UI"
MONO_FONT_FAMILY = "Consolas"


def configure_theme(root: tk.Tk) -> None:
    """
    Apply the shared WatchDog dark theme to ttk widgets.

    Use this once when the desktop app starts, before pages are shown.
    """

    style = ttk.Style(root)

    # 'clam' is much more customisable than Windows' native themes.
    # It allows the dark colours to be applied consistently.
    style.theme_use("clam")

    root.configure(background=ABYSS)

    # General layout widgets.
    style.configure(
        "TFrame",
        background=ABYSS,
    )

    style.configure(
        "App.TFrame",
        background=ABYSS,
    )

    style.configure(
        "Card.TFrame",
        background=DEPTH,
    )

    # Labels.
    style.configure(
        "TLabel",
        background=ABYSS,
        foreground=FROST,
        font=(FONT_FAMILY, 10),
    )

    style.configure(
        "Title.TLabel",
        background=ABYSS,
        foreground=FROST,
        font=(FONT_FAMILY, 22, "bold"),
    )

    style.configure(
        "Subtitle.TLabel",
        background=ABYSS,
        foreground=ASH,
        font=(FONT_FAMILY, 11),
    )

    style.configure(
        "Section.TLabel",
        background=DEPTH,
        foreground=FROST,
        font=(FONT_FAMILY, 11, "bold"),
    )

    style.configure(
        "CardBody.TLabel",
        background=DEPTH,
        foreground=ASH,
        font=(FONT_FAMILY, 10),
    )

    style.configure(
        "Muted.TLabel",
        background=ABYSS,
        foreground=ASH,
        font=(FONT_FAMILY, 10),
    )

    style.configure(
        "Success.TLabel",
        background=DEPTH,
        foreground=EMERALD,
        font=(FONT_FAMILY, 10, "bold"),
    )

    style.configure(
        "Warning.TLabel",
        background=DEPTH,
        foreground=CAUTION,
        font=(FONT_FAMILY, 10, "bold"),
    )

    style.configure(
        "Error.TLabel",
        background=DEPTH,
        foreground=THREAT,
        font=(FONT_FAMILY, 10, "bold"),
    )

    # Card-style LabelFrames.
    style.configure(
        "TLabelframe",
        background=DEPTH,
        bordercolor=GUNMETAL,
        lightcolor=DEPTH,
        darkcolor=DEPTH,
        relief="flat",
    )

    style.configure(
        "TLabelframe.Label",
        background=DEPTH,
        foreground=FROST,
        font=(FONT_FAMILY, 10, "bold"),
    )

    style.configure(
        "Card.TLabelframe",
        background=DEPTH,
        bordercolor=SLATE,
        lightcolor=DEPTH,
        darkcolor=DEPTH,
        relief="flat",
    )

    style.configure(
        "Card.TLabelframe.Label",
        background=DEPTH,
        foreground=FROST,
        font=(FONT_FAMILY, 11, "bold"),
    )

    # Primary Emerald button.
    style.configure(
        "Primary.TButton",
        background=EMERALD,
        foreground=VOID,
        bordercolor=EMERALD,
        lightcolor=EMERALD,
        darkcolor=EMERALD,
        relief="flat",
        padding=(16, 9),
        font=(FONT_FAMILY, 10, "bold"),
    )

    style.map(
        "Primary.TButton",
        background=[
            ("active", "#34D399"),
            ("pressed", "#059669"),
            ("disabled", GUNMETAL),
        ],
        foreground=[
            ("disabled", VOID),
        ],
    )

    # Dark secondary button.
    style.configure(
        "Secondary.TButton",
        background=SLATE,
        foreground=FROST,
        bordercolor=GUNMETAL,
        lightcolor=SLATE,
        darkcolor=SLATE,
        relief="flat",
        padding=(16, 9),
        font=(FONT_FAMILY, 10, "bold"),
    )

    style.map(
        "Secondary.TButton",
        background=[
            ("active", "#2A2A2A"),
            ("pressed", DEPTH),
            ("disabled", DEPTH),
        ],
        foreground=[
            ("disabled", GUNMETAL),
        ],
    )

    # Emergency / destructive button.
    style.configure(
        "Danger.TButton",
        background=THREAT,
        foreground=FROST,
        bordercolor=THREAT,
        lightcolor=THREAT,
        darkcolor=THREAT,
        relief="flat",
        padding=(16, 9),
        font=(FONT_FAMILY, 10, "bold"),
    )

    style.map(
        "Danger.TButton",
        background=[
            ("active", "#F87171"),
            ("pressed", "#DC2626"),
            ("disabled", GUNMETAL),
        ],
    )

    # Inputs.
    style.configure(
        "TEntry",
        fieldbackground=VOID,
        background=VOID,
        foreground=FROST,
        bordercolor=GUNMETAL,
        lightcolor=VOID,
        darkcolor=VOID,
        insertcolor=FROST,
        padding=(10, 8),
        font=(FONT_FAMILY, 10),
    )

    style.map(
        "TEntry",
        bordercolor=[
            ("focus", EMERALD),
        ],
    )

    # Camera table.
    style.configure(
        "Treeview",
        background=DEPTH,
        fieldbackground=DEPTH,
        foreground=FROST,
        bordercolor=SLATE,
        rowheight=36,
        font=(FONT_FAMILY, 10),
    )

    style.map(
        "Treeview",
        background=[
            ("selected", EMERALD),
        ],
        foreground=[
            ("selected", VOID),
        ],
    )

    style.configure(
        "Treeview.Heading",
        background=SLATE,
        foreground=ASH,
        bordercolor=SLATE,
        relief="flat",
        font=(FONT_FAMILY, 10, "bold"),
        padding=(10, 9),
    )

    style.map(
        "Treeview.Heading",
        background=[
            ("active", "#2A2A2A"),
        ],
        foreground=[
            ("active", FROST),
        ],
    )

    # Progress bars.
    style.configure(
        "Horizontal.TProgressbar",
        background=EMERALD,
        troughcolor=SLATE,
        bordercolor=SLATE,
        lightcolor=EMERALD,
        darkcolor=EMERALD,
    )

    # Scrollbars.
    style.configure(
        "Vertical.TScrollbar",
        background=SLATE,
        troughcolor=ABYSS,
        bordercolor=ABYSS,
        arrowcolor=ASH,
    )

    style.map(
        "Vertical.TScrollbar",
        background=[
            ("active", GUNMETAL),
        ],
    )


def configure_log_text_widget(widget: tk.Text) -> None:
    """
    Apply WatchDog dark styling to raw tk.Text / ScrolledText widgets.

    ttk styles cannot control standard Tk text widgets.
    """

    widget.configure(
        background=VOID,
        foreground=FROST,
        insertbackground=FROST,
        selectbackground=SLATE,
        selectforeground=FROST,
        highlightbackground=SLATE,
        highlightcolor=EMERALD,
        relief="flat",
        borderwidth=0,
        padx=12,
        pady=12,
        font=(MONO_FONT_FAMILY, 10),
    )