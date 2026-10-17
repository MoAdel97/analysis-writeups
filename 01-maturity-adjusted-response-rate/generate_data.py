"""
Synthetic direct-mail campaigns where every campaign has the SAME true
response rate, by construction.

That is the whole point. If the true rate is identical everywhere, then any
difference the raw numbers show between a young campaign and an old one is
not performance - it is the measurement being taken too early. A real dataset
can never prove that, because you never know the truth. Here you set it.

    python generate_data.py          ->  data/pieces.csv, data/campaigns.csv
"""
import numpy as np, pandas as pd
from pathlib import Path

SEED        = 11
N_CAMPAIGNS = 80
PIECES_EACH = 5000
TRUE_RATE   = 0.0030          # 0.30% - identical for every campaign
AS_OF       = pd.Timestamp("2026-10-17")

# Reply lag ~ lognormal. Median 13 days, long tail to about three months,
# which is the shape direct mail actually has: a fast first fortnight, then
# a slow tail of people who put the letter on the fridge.
LAG_MU, LAG_SIGMA = np.log(13), 0.95


def main():
    rng = np.random.default_rng(SEED)

    # campaigns land every ~10 days going back about 13 months, so the set
    # contains everything from "mailed last week" to "long finished"
    # geometric spacing, so the set is dense where it matters - the first
    # few weeks, where the measurement problem actually bites
    inhome = [AS_OF - pd.Timedelta(days=int(d))
              for d in np.unique(np.geomspace(3, 400, N_CAMPAIGNS).round())]

    rows = []
    for i, d in enumerate(inhome, start=1):
        age = (AS_OF - d).days
        will_reply = rng.random(PIECES_EACH) < TRUE_RATE
        lag = np.where(will_reply,
                       rng.lognormal(LAG_MU, LAG_SIGMA, PIECES_EACH).round(),
                       np.nan)
        # a reply we have not waited long enough to see is simply not visible
        observed = will_reply & (lag <= age)
        rows.append(pd.DataFrame({
            "campaign_id": f"C{i:03d}",
            "inhome_date": d.date(),
            "days_since_inhome": age,
            "replied_eventually": will_reply.astype(int),
            "reply_lag_days": lag,
            "reply_observed": observed.astype(int),
        }))

    pieces = pd.concat(rows, ignore_index=True)
    Path("data").mkdir(exist_ok=True)
    # only the replies are saved, not all 400k pieces: it is everything both
    # charts need and it keeps the repo small enough to read on GitHub
    (pieces[pieces.replied_eventually == 1]
        [["campaign_id", "days_since_inhome", "reply_lag_days", "reply_observed"]]
        .to_csv("data/replies.csv", index=False))

    camp = (pieces.groupby(["campaign_id", "inhome_date", "days_since_inhome"])
                  .agg(pieces=("reply_observed", "size"),
                       replies_observed=("reply_observed", "sum"),
                       replies_eventual=("replied_eventually", "sum"))
                  .reset_index()
                  .sort_values("days_since_inhome"))
    camp.to_csv("data/campaigns.csv", index=False)

    print(f"{len(pieces):,} pieces across {len(inhome)} campaigns")
    print(f"true rate set to {TRUE_RATE:.3%} for every campaign")
    print(f"observed overall {camp.replies_observed.sum() / camp.pieces.sum():.3%}")
    print(f"eventual overall {camp.replies_eventual.sum() / camp.pieces.sum():.3%}")
    print("\nwrote data/replies.csv and data/campaigns.csv")


if __name__ == "__main__":
    main()
