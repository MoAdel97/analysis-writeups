"""
Score each campaign two ways and see which one tells the truth.

    python analysis.py      ->  charts/*.png  + the numbers quoted in README
"""
import sys; sys.path.insert(0, "../_shared")
import numpy as np, pandas as pd, matplotlib.pyplot as plt
import style
from pathlib import Path

TRUE_RATE = 0.0030

# The business rule: how much of a piece's response window has elapsed.
# Deliberately a coarse step function, not the underlying distribution -
# a warehouse has to compute this in a computed column, and nobody wants a
# lognormal CDF in T-SQL. The steps come from reading the observed curve.
STEPS = [(60, 1.000), (45, 0.924), (30, 0.842), (21, 0.771),
         (14, 0.620), (7, 0.337), (3, 0.114)]


def expected_pct(days):
    for threshold, pct in STEPS:
        if days >= threshold:
            return pct
    return 0.020


def main():
    style.use()
    pieces = pd.read_csv("data/replies.csv")
    camp = pd.read_csv("data/campaigns.csv")

    camp["expected_pct"] = camp.days_since_inhome.map(expected_pct)
    camp["raw_rate"] = camp.replies_observed / camp.pieces
    camp["adj_rate"] = camp.replies_observed / (camp.pieces * camp.expected_pct)

    young = camp[camp.days_since_inhome < 21]
    mature = camp[camp.days_since_inhome >= 60]

    print("                       campaigns   raw rate   adjusted rate")
    for label, d in [("under 21 days", young), ("60 days or more", mature),
                     ("all", camp)]:
        raw = d.replies_observed.sum() / d.pieces.sum()
        adj = d.replies_observed.sum() / (d.pieces * d.expected_pct).sum()
        print(f"  {label:20s} {len(d):6d}   {raw:7.3%}   {adj:11.3%}")
    print(f"\n  true rate, set by the generator: {TRUE_RATE:.3%}")
    sr = camp.raw_rate.std() / camp.raw_rate.mean()
    sa = camp.adj_rate.std() / camp.adj_rate.mean()
    print(f"  spread across campaigns (CV):  raw {sr:.2f}   adjusted {sa:.2f}")

    # ---- chart 1: the response curve the rule is approximating -----------
    lags = pieces["reply_lag_days"].dropna()
    xs = np.arange(0, 121)
    cdf = [(lags <= x).mean() for x in xs]
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    ax.plot(xs, np.array(cdf) * 100, color=style.TEAL, lw=2.5, label="actual replies")
    sx = sorted([s[0] for s in STEPS] + [0, 120])
    sy = [expected_pct(x) * 100 for x in sx]
    ax.step(sx, sy, where="post", color=style.AMBER, lw=2, ls="--",
            label="step rule used in the warehouse")
    med = float(lags.median())
    ax.axvline(med, color=style.MUTED, lw=1, ls=":")
    ax.text(med + 2, 8, f"median day {med:.0f}", color=style.MUTED, fontsize=9)
    ax.set_xlabel("days since the letter landed"); ax.set_ylabel("")
    ax.set_ylim(0, 103); ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
    ax.legend(loc="lower right")
    style.finish(ax, "Replies arrive over about two months",
                 "share of all replies received, by days since the letter landed",
                 "synthetic data, 330,000 pieces · generate_data.py seed 11")
    plt.savefig("charts/response_curve.png", bbox_inches="tight"); plt.close()

    # ---- chart 2: raw vs adjusted, against a known truth ------------------
    YMAX = 0.75
    fig, ax = plt.subplots(figsize=(8.0, 4.4))
    ax.axhline(TRUE_RATE * 100, color=style.INK, lw=1.2, ls="--", zorder=2)
    ax.text(408, TRUE_RATE * 100, "true rate\n0.300%", color=style.INK,
            fontsize=8.5, va="center", ha="left", linespacing=1.3)
    ax.scatter(camp.days_since_inhome, camp.raw_rate * 100, s=46,
               color=style.BRICK, marker="o", label="raw rate", zorder=4)
    ax.scatter(camp.days_since_inhome, camp.adj_rate * 100, s=40,
               facecolors="none", edgecolors=style.TEAL, linewidths=1.8,
               marker="D", label="maturity-adjusted", zorder=5)
    off = camp[camp.adj_rate * 100 > YMAX].sort_values("days_since_inhome")
    if len(off):
        vals = " and ".join(f"{v*100:.2f}%" for v in off.adj_rate)
        ax.text(0.33, 0.95, f"{len(off)} campaigns under a week old sit\n"
                            f"off this scale, at {vals}",
                transform=ax.transAxes, fontsize=8.5, color=style.TEAL,
                va="top", linespacing=1.4)
    ax.set_xlabel("campaign age in days"); ax.set_ylabel("")
    ax.set_ylim(0, YMAX); ax.set_xlim(-8, 405)
    ax.yaxis.set_major_formatter(lambda v, p: f"{v:.2f}%")
    ax.legend(loc="upper right")
    style.finish(ax, "Every campaign here has the same true response rate",
                 "raw scoring punishes a young campaign for nothing but being young",
                 "synthetic data, 330,000 pieces \u00b7 true rate fixed at 0.300% by construction")
    plt.savefig("charts/raw_vs_adjusted.png", bbox_inches="tight"); plt.close()

    camp.to_csv("data/campaigns_scored.csv", index=False)
    print("\nwrote charts/response_curve.png, charts/raw_vs_adjusted.png")


if __name__ == "__main__":
    main()
