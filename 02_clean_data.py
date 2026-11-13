# step 2: one peril in one state, grouped into storm days
import sys

import pandas as pd

import config

# columns I need (NOAA has them in capitals, I lower them after reading)
WANTED = ["state", "year", "event_type", "begin_date_time", "damage_property"]


def damage_to_dollars(text):
    # damage is text like 10.00K or 2.5M
    text = str(text).strip().upper()
    if text in ("", "NAN"):
        return 0.0
    factor = 1.0
    if text[-1] == "K":
        factor = 1_000.0
    elif text[-1] == "M":
        factor = 1_000_000.0
    elif text[-1] == "B":
        factor = 1_000_000_000.0
    if text[-1] in "KMB":
        text = text[:-1]
    try:
        return float(text) * factor
    except ValueError:
        return 0.0


parts = []
files = sorted(config.RAW_DIR.glob("StormEvents_details*.csv.gz"))
if not files:
    sys.exit("No files in data/raw. Run 01_download_data.py first.")

for file in files:
    df = pd.read_csv(file, usecols=lambda c: c.lower() in WANTED, low_memory=False)
    df.columns = [c.lower() for c in df.columns]

    # only my peril and my state
    df = df[(df["event_type"].str.strip().str.lower() == config.PERIL.lower())
            & (df["state"].str.strip().str.upper() == config.STATE.upper())]
    parts.append(df)

records = pd.concat(parts)
print("Records for", config.PERIL, "in", config.STATE, ":", len(records))

records["damage_usd"] = records["damage_property"].apply(damage_to_dollars)
records["storm_date"] = pd.to_datetime(records["begin_date_time"],
                                       format="mixed", errors="coerce")

# dates come in more than one style, stop if too many cannot be read
bad_dates = records["storm_date"].isna().sum()
print("Dates that could not be read:", bad_dates)
if bad_dates > 0.01 * len(records):
    sys.exit("Too many unreadable dates. Look at the begin_date_time column.")
records = records.dropna(subset=["storm_date"])
records["storm_date"] = records["storm_date"].dt.normalize()

# lots of records have no damage written down, those are dropped
with_damage = records[records["damage_usd"] > 0]
print("Records with damage above zero:", len(with_damage))

# one storm gives several records (one per county), so I add them up per day
# one row = one damaging storm day in the state
storm_days = (with_damage.groupby("storm_date")
              .agg(damage_usd=("damage_usd", "sum"),
                   n_records=("damage_usd", "size"))
              .reset_index())
storm_days["year"] = storm_days["storm_date"].dt.year
storm_days = storm_days[(storm_days["year"] >= config.FIRST_YEAR)
                        & (storm_days["year"] <= config.LAST_YEAR)]

print("Damaging storm days:", len(storm_days))
print(storm_days.groupby("year").size().to_string())

if len(storm_days) < 50:
    sys.exit("Fewer than 50 storm days. Change PERIL or STATE in config.py.")

storm_days.to_csv(config.CLEAN_FILE, index=False)
print("Saved", config.CLEAN_FILE)
