"""
ProgramEval - synthetic data generator.

Simulates a government-funded youth employment program ("Pathways to Work")
with a treatment group (received the program) and a comparison group (did not).
Each participant has baseline characteristics and a 6-month employment outcome.

The data has a real (modest) program effect plus selection noise, so the
evaluation has to separate genuine impact from baseline differences -
exactly the challenge in program / outcome evaluation.

All data is synthetic.
"""

from __future__ import annotations
import sqlite3
from pathlib import Path
import numpy as np
import pandas as pd

RNG = np.random.default_rng(2024)
DATA_DIR = Path(__file__).parent / "data"
N = 1500
REGIONS = ["Metro North", "Metro South", "Regional", "Remote"]


def generate() -> pd.DataFrame:
    rows = []
    for i in range(N):
        treated = int(RNG.random() < 0.5)
        age = int(RNG.integers(17, 25))
        region = RNG.choice(REGIONS, p=[0.30, 0.30, 0.25, 0.15])
        prior_unemployed_months = int(RNG.gamma(2.0, 3.0))
        has_yr12 = int(RNG.random() < 0.55)

        # Baseline probability of employment at 6 months (no program).
        base = (0.18
                + 0.04 * has_yr12
                - 0.012 * min(prior_unemployed_months, 18)
                + 0.01 * (age - 17)
                + (0.05 if region.startswith("Metro") else -0.03))
        # True program effect: +11 percentage points, larger for long-term unemployed.
        effect = 0.11 + (0.05 if prior_unemployed_months > 6 else 0.0)
        p = np.clip(base + treated * effect, 0.02, 0.95)
        employed = int(RNG.random() < p)

        # Cost per participant (program group costs more).
        cost = (RNG.normal(4200, 600) if treated else RNG.normal(350, 120))
        rows.append([f"P{i:05d}", treated, age, region,
                     prior_unemployed_months, has_yr12, employed, round(cost, 2)])

    return pd.DataFrame(rows, columns=[
        "participant_id", "treated", "age", "region",
        "prior_unemployed_months", "has_year12", "employed_6m", "cost_aud"])


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    df = generate()
    df.to_csv(DATA_DIR / "participants.csv", index=False)
    con = sqlite3.connect(DATA_DIR / "program.db")
    df.to_sql("participants", con, if_exists="replace", index=False)
    con.close()
    print(f"Wrote {len(df)} participants to data/participants.csv and data/program.db")


if __name__ == "__main__":
    main()
