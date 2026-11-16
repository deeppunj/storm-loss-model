# step 9: compare the model's answers with the numbers NOAA filled in
import pandas as pd

import config

reports = pd.read_csv(config.NARRATIVES_FILE)
print("Prompt version", config.PROMPT_VERSION)
answers = pd.read_csv(config.results_file("llm_answers"), dtype={"llm_rating": str})
both = answers.merge(reports, on="event_id")
print("Reports compared:", len(both))
print("Replies the model did not fill in:", both["llm_injured"].isna().sum())

both["noaa_injured"] = both["injuries_direct"] > 0
both["noaa_killed"] = both["deaths_direct"] > 0
both["model_injured"] = both["llm_injured"] == "yes"
both["model_killed"] = both["llm_killed"] == "yes"

rows = []
for field in ["injured", "killed"]:
    noaa = both["noaa_" + field]
    model = both["model_" + field]
    # recall: of the reports NOAA counts with injuries, how many the model found
    # precision: of the reports the model says yes, how many NOAA agrees with
    rows.append({"question": field,
                 "reports": len(both),
                 "agreement_pct": 100 * (noaa == model).mean(),
                 "noaa_yes": int(noaa.sum()),
                 "model_yes": int(model.sum()),
                 "both_yes": int((noaa & model).sum()),
                 "recall_pct": 100 * (noaa & model).sum() / noaa.sum() if noaa.sum() else None,
                 "precision_pct": 100 * (noaa & model).sum() / model.sum() if model.sum() else None})

# rating: only where NOAA gives a rating and the model read one from the text
both["model_rating"] = pd.to_numeric(both["llm_rating"], errors="coerce")
rated = both.dropna(subset=["noaa_rating", "model_rating"])
rows.append({"question": "rating (where both give one)",
             "reports": len(rated),
             "agreement_pct": 100 * (rated["noaa_rating"] == rated["model_rating"]).mean()})
print("Reports with a NOAA rating where the model found none in the text:",
      int((both["noaa_rating"].notna() & both["model_rating"].isna()).sum()))

table = pd.DataFrame(rows).round(1)
for col in ["noaa_yes", "model_yes", "both_yes"]:
    table[col] = table[col].astype("Int64")   # whole numbers, empty for the rating row
print(table.to_string(index=False))
table.to_csv(config.results_file("llm_agreement"), index=False)

# NOAA's injury count does not always come from the text. A simple word search
# shows which injury reports mention an injury at all, so I can see how often the
# model finds an injury that is written down, and how often it says yes without one
both["text_mentions_injury"] = both["event_narrative"].str.contains(
    r"injur|hurt|hospital|wound", case=False)
noaa_injured = both[both["noaa_injured"]]
text_check = (noaa_injured.groupby("text_mentions_injury")
              .agg(reports=("event_id", "size"), model_yes=("model_injured", "sum"))
              .reset_index())
text_check["model_yes_pct"] = (100 * text_check["model_yes"] / text_check["reports"]).round(1)
print()
print("Reports NOAA counts with an injury, split by whether the text mentions one:")
print(text_check.to_string(index=False))
text_check.to_csv(config.results_file("llm_injury_text_check"), index=False)
print()

# the reports where the two disagree, to read by hand
wrong = both[(both["noaa_injured"] != both["model_injured"])
             | (both["noaa_killed"] != both["model_killed"])
             | ((both["noaa_rating"] != both["model_rating"])
                & both["noaa_rating"].notna() & both["model_rating"].notna())]
wrong = wrong[["event_id", "year", "injuries_direct", "llm_injured", "deaths_direct",
               "llm_killed", "tor_f_scale", "llm_rating", "event_narrative"]]
wrong.insert(len(wrong.columns), "my_note", "")   # I fill this in after reading
wrong.to_csv(config.results_file("llm_disagreements"), index=False)
print("Disagreements:", len(wrong), "saved in", config.results_file("llm_disagreements").name)

# only for the first prompt: random false alarms (model says injured, NOAA says
# nobody) that I read to write prompt 2. Not written again if the file is there,
# so my notes in it are kept
check_file = config.RESULTS_DIR / "false_alarm_check.csv"
if config.PROMPT_VERSION == 1 and check_file.exists():
    print("Kept", check_file.name, "(delete it to pick them again)")
elif config.PROMPT_VERSION == 1:
    false_alarms = wrong[(wrong["injuries_direct"] == 0) & (wrong["llm_injured"] == "yes")]
    check = false_alarms.sample(config.N_FALSE_ALARMS_TO_READ, random_state=config.RANDOM_SEED)
    check = check[["event_id", "year", "injuries_direct", "llm_injured", "event_narrative"]]
    check.insert(len(check.columns), "my_note", "")
    check.to_csv(check_file, index=False)
    print("Saved", len(check), "false alarms to read in", check_file.name)

# both versions side by side, once both have been checked
v1 = config.RESULTS_DIR / "llm_agreement_v1.csv"
v2 = config.RESULTS_DIR / "llm_agreement_v2.csv"
if v1.exists() and v2.exists():
    both_versions = pd.concat([pd.read_csv(v1).assign(prompt=1), pd.read_csv(v2).assign(prompt=2)])
    both_versions = both_versions[["question", "prompt", "reports", "agreement_pct",
                                   "model_yes", "both_yes", "recall_pct", "precision_pct"]]
    both_versions = both_versions.sort_values(["question", "prompt"])
    for col in ["model_yes", "both_yes"]:
        both_versions[col] = both_versions[col].astype("Int64")
    print()
    print(both_versions.to_string(index=False))
    both_versions.to_csv(config.RESULTS_DIR / "llm_prompt_comparison.csv", index=False)
    print("Saved llm_prompt_comparison.csv")
