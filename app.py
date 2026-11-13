# dashboard, start with: streamlit run app.py
import json

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

import config
import model_functions as mf

st.title(f"{config.PERIL} losses in {config.STATE.title()}")
st.write("A small model built from NOAA Storm Events records. "
         "It is a personal project on public data, not an insurance model. "
         "Dollar values are not adjusted for inflation.")

with open(config.PARAMS_FILE) as f:
    params = json.load(f)
freq, sev = params["frequency"], params["severity"]
storm_days = mf.load_storm_days()
table = mf.yearly_table(storm_days)

st.sidebar.header("Assumptions")
kind = st.sidebar.radio("How to draw the damage of a storm day",
                        ["lognormal", "bootstrap"],
                        format_func=lambda k: "Lognormal curve" if k == "lognormal"
                        else "Real storm days")
freq_factor = st.sidebar.slider("Storm days per year, compared with history", 0.5, 1.5, 1.0, 0.05)
sev_factor = st.sidebar.slider("Damage per storm day, compared with history", 0.5, 1.5, 1.0, 0.05)

rng = np.random.default_rng(config.RANDOM_SEED)
losses = mf.simulate_years(freq, sev, 50000, rng, kind, storm_days["damage_usd"].values,
                           freq_factor, sev_factor)

left, right = st.columns(2)
left.metric("Average year", mf.money(losses.mean()))
right.metric("1-in-100 year", mf.money(np.quantile(losses, 0.99)))

periods = np.logspace(np.log10(1.2), 3, 40)
curve = [np.quantile(losses, 1 - 1 / t) / 1e6 for t in periods]
real = np.sort(table["total_damage"].values)[::-1]
real_periods = (len(real) + 1) / np.arange(1, len(real) + 1)

fig, ax = plt.subplots(figsize=(7, 4))
ax.plot(periods, curve, color="#2a78d6", linewidth=2, label="Model")
ax.scatter(real_periods, real / 1e6, color="#52514e", s=22, label="Real years")
ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlabel("Return period in years (1 in N)")
ax.set_ylabel("Yearly loss, million USD")
ax.legend(frameon=False)
ax.grid(alpha=0.2)
st.pyplot(fig)

st.subheader("Real history by year")
st.dataframe(table)
