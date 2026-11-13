# functions the other scripts use
import numpy as np
import pandas as pd

import config

RETURN_PERIODS = [2, 5, 10, 20, 50, 100, 200]


def load_storm_days():
    return pd.read_csv(config.CLEAN_FILE, parse_dates=["storm_date"])


def yearly_table(storm_days):
    # one row per year, years without a storm day get 0
    # (without this the average number of storm days comes out too high)
    years = range(config.FIRST_YEAR, config.LAST_YEAR + 1)
    table = storm_days.groupby("year").agg(storm_days=("damage_usd", "size"),
                                           total_damage=("damage_usd", "sum"))
    table = table.reindex(years, fill_value=0)
    table.index.name = "year"
    return table


def fit_frequency(counts):
    # counts = storm days per year
    mean = counts.mean()
    variance = counts.var(ddof=1)
    if variance > mean:
        # poisson needs variance = mean, so use negative binomial
        # (method of moments)
        p = mean / variance
        n = mean * p / (1 - p)
        return {"type": "negative_binomial", "n": n, "p": p,
                "mean": mean, "variance": variance}
    return {"type": "poisson", "mean": mean, "variance": variance}


def fit_severity(damages):
    # damage is very skewed, so lognormal: normal curve on the log of the damage
    logs = np.log(damages)
    return {"mu": logs.mean(), "sigma": logs.std(ddof=1)}


def simulate_years(freq, sev, n_years, rng, severity_kind="lognormal",
                   history=None, freq_factor=1.0, sev_factor=1.0):
    # storm days per simulated year
    mean = freq["mean"] * freq_factor
    if freq["type"] == "poisson":
        counts = rng.poisson(mean, n_years)
    else:
        # keep n, change the mean through p
        p = freq["n"] / (freq["n"] + mean)
        counts = rng.negative_binomial(freq["n"], p, n_years)

    # one damage for every storm day of all years
    total_days = counts.sum()
    if severity_kind == "lognormal":
        damages = rng.lognormal(sev["mu"], sev["sigma"], total_days)
    else:
        # bootstrap: draw from the real storm days
        damages = rng.choice(history, total_days)
    damages = damages * sev_factor

    # add up per year
    year_number = np.repeat(np.arange(n_years), counts)
    return np.bincount(year_number, weights=damages, minlength=n_years)


def loss_at_return_periods(yearly_losses):
    # 1 in T years = quantile 1 - 1/T (1 in 100 = 99th percentile)
    return {t: np.quantile(yearly_losses, 1 - 1 / t) for t in RETURN_PERIODS}


def money(x):
    return f"${x / 1e6:,.1f}M"
