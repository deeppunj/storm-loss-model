# step 5: simulate years with two model versions, draw the loss curve
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

storm_days = mf.load_storm_days()
table = mf.yearly_table(storm_days)
history = storm_days["damage_usd"].values

rng = np.random.default_rng(config.RANDOM_SEED)
n = config.N_SIMULATED_YEARS

# A: damage from the lognormal, B: damage drawn from the real storm days
version_a = mf.simulate_years(freq, sev, n, rng, "lognormal")
version_b = mf.simulate_years(freq, sev, n, rng, "bootstrap", history)

# summary table
rows = []
for name, losses in [("A: lognormal", version_a), ("B: real storm days", version_b)]:
    row = {"version": name, "average_year": losses.mean()}
    for t, value in mf.loss_at_return_periods(losses).items():
        row[f"1_in_{t}"] = value
    rows.append(row)
real_row = {"version": "Real history", "average_year": table["total_damage"].mean()}
rows.append(real_row)
summary = pd.DataFrame(rows)
summary.to_csv(config.RESULTS_DIR / "loss_summary.csv", index=False)

print("Dollar values are not adjusted for inflation.\n")
print(summary.to_string(index=False, float_format=lambda x: f"{x:,.0f}"))

# chart
periods = np.logspace(np.log10(1.2), 3, 40)
fig, ax = plt.subplots(figsize=(7, 4.2))
for losses, label, color in [(version_a, "Version A (lognormal)", "#2a78d6"),
                             (version_b, "Version B (real storm days)", "#eb6834")]:
    curve = [np.quantile(losses, 1 - 1 / t) / 1e6 for t in periods]
    ax.plot(periods, curve, label=label, color=color, linewidth=2)

# real years: the biggest of N years is roughly a 1-in-(N+1) year
real = np.sort(table["total_damage"].values)[::-1]
real_periods = (len(real) + 1) / np.arange(1, len(real) + 1)
ax.scatter(real_periods, real / 1e6, color="#52514e", s=22, zorder=3,
           label=f"Real years ({len(real)} years)")

ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlabel("Return period in years (1 in N)")
ax.set_ylabel("Yearly loss, million USD")
ax.set_title(f"{config.PERIL} loss curve, {config.STATE.title()}")
ax.legend(frameon=False)
ax.grid(alpha=0.2)
for side in ("top", "right"):
    ax.spines[side].set_visible(False)
fig.tight_layout()
fig.savefig(config.RESULTS_DIR / "loss_curve.png", dpi=150)
print("\nSaved results/loss_curve.png")
