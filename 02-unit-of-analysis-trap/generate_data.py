"""
Synthetic mailing data in which repeat contact DOES NOT EXIST.

Every letter to a property is posted on the same day, to a different person
at that address. There is no second touch anywhere in this dataset - not one
property is ever mailed twice in time. That is the point: whatever the
"letter number" analysis appears to show, it cannot be a touch effect,
because there are no touches to have an effect.

    python generate_data.py   ->  data/letters.csv, data/properties.csv
"""
import numpy as np, pandas as pd
from pathlib import Path

SEED         = 7
N_PROPERTIES = 250_000
MAIL_DATE    = "2026-03-02"          # one date. for every single letter.

# How many contactable people skip-tracing found at the property.
CONTACTS_P = {1: 0.70, 2: 0.15, 3: 0.08, 4: 0.07}

# Per-LETTER reply probability, by how many contacts were found.
# A property where more people could be traced is a more reachable property:
# the estate is active, the records are current, someone answers a phone.
# Note this depends on the PROPERTY, never on which letter it is.
REPLY_P = {1: 0.0022, 2: 0.0036, 3: 0.0040, 4: 0.0042}


def main():
    rng = np.random.default_rng(SEED)
    ks = np.array(list(CONTACTS_P)); ps = np.array(list(CONTACTS_P.values()))
    contacts = rng.choice(ks, size=N_PROPERTIES, p=ps)

    rows = []
    for k in ks:
        idx = np.flatnonzero(contacts == k)
        n = len(idx)
        for pos in range(1, k + 1):
            replied = rng.random(n) < REPLY_P[k]
            rows.append(pd.DataFrame({
                "property_id": idx,
                "contacts_found": k,
                "letter_no": pos,          # position within the property, arbitrary
                "mail_date": MAIL_DATE,    # identical for all of them
                "replied": replied.astype(int),
            }))

    letters = pd.concat(rows, ignore_index=True)
    Path("data").mkdir(exist_ok=True)

    # aggregate rather than ship 380k rows - the analysis only needs these
    (letters.groupby(["contacts_found", "letter_no"])
            .agg(letters=("replied", "size"), replies=("replied", "sum"))
            .reset_index()
            .to_csv("data/letters.csv", index=False))

    props = (letters.groupby(["property_id", "contacts_found"])
                    .agg(letters=("replied", "size"), replies=("replied", "sum"))
                    .reset_index())
    props["replied_any"] = (props.replies > 0).astype(int)
    (props.groupby("contacts_found")
          .agg(properties=("replied_any", "size"), replied=("replied_any", "sum"))
          .reset_index()
          .to_csv("data/properties.csv", index=False))

    print(f"{len(letters):,} letters to {N_PROPERTIES:,} properties")
    print(f"distinct mail dates in the whole file: {letters.mail_date.nunique()}")
    print(f"overall reply rate per letter: {letters.replied.mean():.3%}")
    print("\nwrote data/letters.csv and data/properties.csv")


if __name__ == "__main__":
    main()
