"""Shared chart style. One import, so every chart in the repo matches.

The three series colours are checked against a colourblind simulation at this
lightness: deutan and tritan separation above the usual Delta-E 8 floor, and
each one sits inside the readable lightness band against a white page. Amber
falls below 3:1 contrast, so anything drawn in amber is always directly
labelled rather than left to the legend.
"""
import matplotlib as mpl
import matplotlib.pyplot as plt

TEAL, BRICK, AMBER = "#00806B", "#C9503C", "#E2A32D"
INK, MUTED, RULE = "#1A1713", "#6B655C", "#E0D9CB"
SERIES = [TEAL, BRICK, AMBER, "#4A6FA5", "#7A6A8F"]


def use():
    mpl.rcParams.update({
        "figure.facecolor": "white", "axes.facecolor": "white",
        "font.family": "DejaVu Sans", "font.size": 10,
        "axes.edgecolor": RULE, "axes.labelcolor": INK, "text.color": INK,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": RULE, "grid.linewidth": 0.8,
        "axes.axisbelow": True,
        "xtick.color": MUTED, "ytick.color": MUTED,
        "xtick.bottom": True, "ytick.left": False,
        "axes.prop_cycle": mpl.cycler(color=SERIES),
        "legend.frameon": False, "figure.dpi": 140,
    })


def finish(ax, title, subtitle=None, source=None):
    """Title above the plot, subtitle under it, source note at the foot."""
    ax.set_title("")
    y = 1.04 if subtitle else 1.02
    ax.text(0, y + (0.06 if subtitle else 0), title, transform=ax.transAxes,
            fontsize=12.5, fontweight="bold", color=INK, va="bottom")
    if subtitle:
        ax.text(0, y - 0.01, subtitle, transform=ax.transAxes,
                fontsize=9.5, color=MUTED, va="bottom")
    if source:
        ax.text(0, -0.17, source, transform=ax.transAxes,
                fontsize=8.5, color=MUTED, va="top")
    plt.tight_layout()
