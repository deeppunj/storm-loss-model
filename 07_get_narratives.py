# step 7: the written reports (narratives) for the same tornadoes
import sys

import pandas as pd

import config
from model_functions import damage_to_dollars

# the narrative is the text the weather office writes for each record.
# NOAA also fills in injuries, deaths and the EF rating as numbers,
# so I can later check what the language model reads from the text
WANTED = ["event_id", "state", "year", "event_type", "event_narrative",
          "injuries_direct", "deaths_direct", "tor_f_scale", "damage_property"]

parts = []
files = sorted(config.RAW_DIR.glob("StormEvents_details*.csv.gz"))
if not files:
    sys.exit("No files in data/raw. Run 01_download_data.py first.")

for file in files:
    df = pd.read_csv(file, usecols=lambda c: c.lower() in WANTED, low_memory=False)
    df.columns = [c.lower() for c in df.columns]
    df = df[(df["event_type"].str.strip().str.lower() == config.PERIL.lower())
            & (df["state"].str.strip().str.upper() == config.STATE.upper())]
    parts.append(df)

reports = pd.concat(parts)
reports = reports[(reports["year"] >= config.FIRST_YEAR)
                  & (reports["year"] <= config.LAST_YEAR)]
print("Records:", len(reports))

# a few records have no text, nothing to read there
reports = reports.dropna(subset=["event_narrative"])
reports["event_narrative"] = reports["event_narrative"].str.strip()
reports = reports[reports["event_narrative"] != ""]
print("Records with a narrative:", len(reports))

reports["damage_usd"] = reports["damage_property"].apply(damage_to_dollars)

# EF rating as a number 0 to 5. Before 2007 NOAA used the old F scale (F0, F1, ...),
# I keep only the digit. EFU means not rated, that becomes empty
reports["noaa_rating"] = pd.to_numeric(
    reports["tor_f_scale"].astype(str).str.extract(r"([0-5])")[0], errors="coerce")

# sample for the language model. Injuries are rare (about 6% of records),
# so a random sample would have only a few of them and say little.
# I take every record with an injury and fill up with random other records
injured = reports[reports["injuries_direct"] > 0]
others = reports[reports["injuries_direct"] == 0]
n_others = config.N_LLM_SAMPLE - len(injured)
if n_others < 0:
    sys.exit("More injury records than N_LLM_SAMPLE. Raise N_LLM_SAMPLE in config.py.")
picked = others.sample(n=n_others, random_state=config.RANDOM_SEED)
reports["in_llm_sample"] = reports["event_id"].isin(
    pd.concat([injured, picked])["event_id"])

print("Records with an injury:", len(injured))
print("Records in the language model sample:", reports["in_llm_sample"].sum())

keep = ["event_id", "year", "event_narrative", "injuries_direct", "deaths_direct",
        "tor_f_scale", "noaa_rating", "damage_usd", "in_llm_sample"]
reports[keep].to_csv(config.NARRATIVES_FILE, index=False)
print("Saved", config.NARRATIVES_FILE)
