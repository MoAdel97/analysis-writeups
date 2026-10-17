"""
Cut the same data two ways: by letter number, and by the property.

    python analysis.py   ->  charts/*.png + the numbers quoted in README
"""
import sys; sys.path.insert(0, "../_shared")
import pandas as pd, matplotlib.pyplot as plt
from scipy import stats
import style


def wilson(k, n):
    lo, hi = stats.binomtest(int(k), int(n)).proportion_ci(0.95, method="wilson")
    return lo * 100, hi * 100


def main():
    style.use()
    letters = pd.read_csv("data/letters.csv")
    props = pd.read_csv("data/properties.csv")

    # ---- the trap: rate by letter number ---------------------------------
    by_no = (letters.groupby("letter_no")
                    .agg(letters=("letters", "sum"), replies=("replies", "sum"))
                    .reset_index())
    by_no["rate"] = by_no.replies / by_no.letters * 100
    by_no[["lo", "hi"]] = [wilson(r.replies, r.letters) for r in by_no.itertuples()]

    print("BY LETTER NUMBER  (the trap)")
    print(f"{'letter':>7} {'letters':>9} {'replies':>8} {'rate':>8}   95% CI")
    for r in by_no.itertuples():
        print(f"{r.letter_no:>7} {r.letters:>9,} {r.replies:>8,} {r.rate:>7.3f}%"
              f"   {r.lo:.3f}-{r.hi:.3f}%")
    lift = by_no.rate.iloc[-1] / by_no.rate.iloc[0]
    print(f"  apparent lift, letter 1 -> 4: {lift:.2f}x")

    # ---- the real driver: the property -----------------------------------
    props["rate"] = props.replied / props.properties * 100
    props[["lo", "hi"]] = [wilson(r.replied, r.properties) for r in props.itertuples()]
    print("\nBY CONTACTS FOUND AT THE PROPERTY  (the real driver)")
    print(f"{'contacts':>9} {'properties':>11} {'replied':>8} {'rate':>8}   95% CI")
    for r in props.itertuples():
        print(f"{r.contacts_found:>9} {r.properties:>11,} {r.replied:>8,} {r.rate:>7.3f}%"
              f"   {r.lo:.3f}-{r.hi:.3f}%")
    pl = props.rate.iloc[-1] / props.rate.iloc[0]
    print(f"  property-level lift, 1 -> 4 contacts: {pl:.2f}x")

    # ---- per-letter rate, holding contacts fixed -------------------------
    print("\nPER-LETTER RATE WITHIN EACH CONTACT COUNT")
    print("(flat across letter_no is what 'no touch effect' looks like)")
    piv = letters.pivot_table(index="contacts_found", columns="letter_no",
                              values=["letters", "replies"], aggfunc="sum")
    rate = (piv["replies"] / piv["letters"] * 100).round(3)
    print(rate.fillna("").to_string())

    # ---- chart 1 ---------------------------------------------------------
    fig, ax = plt.subplots(figsize=(7.0, 4.0))
    ax.bar(by_no.letter_no, by_no.rate, color=style.BRICK, width=0.62, zorder=3)
    ax.errorbar(by_no.letter_no, by_no.rate,
                yerr=[by_no.rate - by_no.lo, by_no.hi - by_no.rate],
                fmt="none", ecolor=style.INK, elinewidth=1.2, capsize=4, zorder=4)
    for r in by_no.itertuples():
        ax.text(r.letter_no, r.hi + 0.012, f"{r.rate:.3f}%", ha="center",
                fontsize=9, color=style.INK)
    ax.set_xticks(by_no.letter_no); ax.set_xlabel("letter number at the property")
    ax.set_ylim(0, by_no.hi.max() * 1.22)
    ax.yaxis.set_major_formatter(lambda v, p: f"{v:.2f}%")
    style.finish(ax, "Reply rate rises with the number of letters sent",
                 "which looks like proof that mailing again works",
                 "synthetic data · every letter in this file was posted on the same day")
    plt.savefig("charts/by_letter_number.png", bbox_inches="tight"); plt.close()

    # ---- chart 2 ---------------------------------------------------------
    fig, ax = plt.subplots(figsize=(7.0, 4.0))
    ax.bar(props.contacts_found, props.rate, color=style.TEAL, width=0.62, zorder=3)
    ax.errorbar(props.contacts_found, props.rate,
                yerr=[props.rate - props.lo, props.hi - props.rate],
                fmt="none", ecolor=style.INK, elinewidth=1.2, capsize=4, zorder=4)
    for r in props.itertuples():
        ax.text(r.contacts_found, r.hi + 0.04, f"{r.rate:.2f}%", ha="center",
                fontsize=9, color=style.INK)
    ax.set_xticks(props.contacts_found)
    ax.set_xlabel("people traced at the property")
    ax.set_ylim(0, props.hi.max() * 1.22)
    ax.yaxis.set_major_formatter(lambda v, p: f"{v:.1f}%")
    style.finish(ax, "The same data, asked about the property instead",
                 f"share of properties that replied at all · {pl:.1f}× from one "
                 f"traced contact to four",
                 "synthetic data · intervals are Wilson 95%")
    plt.savefig("charts/by_contacts_found.png", bbox_inches="tight"); plt.close()
    print("\nwrote both charts")


if __name__ == "__main__":
    main()
