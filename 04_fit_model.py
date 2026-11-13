# step 4: fit frequency and severity to the real history
import json

import config
import model_functions as mf

storm_days = mf.load_storm_days()
table = mf.yearly_table(storm_days)

freq = mf.fit_frequency(table["storm_days"])
sev = mf.fit_severity(storm_days["damage_usd"])

print("Years in the data:", len(table))
print("Years with no damaging storm day:", (table["storm_days"] == 0).sum())
print()
print("Storm days per year: mean", round(freq["mean"], 2),
      "variance", round(freq["variance"], 2))
print("Model chosen for frequency:", freq["type"])
print()
print("Damage per storm day: median", mf.money(storm_days["damage_usd"].median()),
      "mean", mf.money(storm_days["damage_usd"].mean()),
      "largest", mf.money(storm_days["damage_usd"].max()))
print("Lognormal parameters: mu", round(sev["mu"], 3), "sigma", round(sev["sigma"], 3))

config.RESULTS_DIR.mkdir(exist_ok=True)
with open(config.PARAMS_FILE, "w") as f:
    json.dump({"frequency": freq, "severity": sev}, f, indent=2)
print("\nSaved", config.PARAMS_FILE)
