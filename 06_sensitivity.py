# step 6: sensitivity to the assumptions, and is 100,000 years enough
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import config
import model_functions as mf

with open(config.PARAMS_FILE) as f:
    params = json.load(f)
freq, sev = params["frequency"], params["severity"]
n = config.N_SIMULATED_YEARS


def run(freq_factor=1.0, sev_factor=1.0, seed=config.RANDOM_SEED, years=n):
    rng = np.random.default_rng(seed)
    losses = mf.simulate_years(freq, sev, years, rng, "lognormal",
                               freq_factor=freq_factor, sev_factor=sev_factor)
    return losses.mean(), np.quantile(losses, 0.99)


# part 1: change one thing at a time
base_average, base_100 = run()
cases = [("Base case", 1.0, 1.0),
         ("20% fewer storm days", 0.8, 1.0),
         ("20% more storm days", 1.2, 1.0),
         ("Damage per storm day 20% lower", 1.0, 0.8),
         ("Damage per storm day 20% higher", 1.0, 1.2)]
rows = []
for name, ff, sf in cases:
    average, one_in_100 = run(ff, sf)
    rows.append({"case": name, "average_year": average, "1_in_100": one_in_100,
                 "average_change_pct": 100 * (average / base_average - 1),
                 "1_in_100_change_pct": 100 * (one_in_100 / base_100 - 1)})
sens = pd.DataFrame(rows)
sens.to_csv(config.RESULTS_DIR / "sensitivity.csv", index=False)
print("Part 1: moving one assumption at a time\n")
print(sens.to_string(index=False, float_format=lambda x: f"{x:,.1f}"))

# part 2: same model, different seeds and sizes
# if the 1-in-100 jumps around the simulation is too small
print("\nPart 2: is the simulation big enough? (1-in-100, million USD)\n")
rows = []
for years in [1000, 10000, 100000]:
    values = [run(seed=s, years=years)[1] / 1e6 for s in range(5)]
    rows.append({"simulated_years": years, "lowest": min(values), "highest": max(values)})
    print(f"{years:>7} years: from {min(values):,.1f} to {max(values):,.1f}")
pd.DataFrame(rows).to_csv(config.RESULTS_DIR / "simulation_size_check.csv", index=False)

# chart for part 1
fig, ax = plt.subplots(figsize=(7, 3.6))
plot = sens[sens["case"] != "Base case"]
ax.barh(plot["case"], plot["1_in_100_change_pct"], color="#2a78d6", height=0.5)
ax.axvline(0, color="#52514e", linewidth=1)
ax.set_xlabel("Change in the 1-in-100 loss, %")
ax.set_title("What moves the 1-in-100 loss")
ax.invert_yaxis()
for side in ("top", "right"):
    ax.spines[side].set_visible(False)
fig.tight_layout()
fig.savefig(config.RESULTS_DIR / "sensitivity.png", dpi=150)
print("\nSaved results/sensitivity.png")
