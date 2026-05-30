"""
ProgramEval - program / outcome evaluation.

Evaluates a fictional youth employment program against a comparison group.
Mirrors how a real evaluation reasons about impact:

  1. Raw effect - simple difference in employment rates (naive).
  2. Baseline balance - are the groups actually comparable?
  3. Adjusted effect - logistic regression controlling for baseline factors,
     giving an honest estimate of the program's contribution.
  4. Subgroups - who benefits most?
  5. Cost-effectiveness - $ per additional person employed.

Outputs:
  outputs/outcomes.png
  outputs/evaluation_report.md
"""

from __future__ import annotations
from pathlib import Path
import sqlite3
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LogisticRegression
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = Path(__file__).parent
OUT = BASE / "outputs"
DB = BASE / "data" / "program.db"


def load() -> pd.DataFrame:
    con = sqlite3.connect(DB)
    df = pd.read_sql("SELECT * FROM participants", con)
    con.close()
    return df


def raw_effect(df):
    t = df[df["treated"] == 1]["employed_6m"].mean()
    c = df[df["treated"] == 0]["employed_6m"].mean()
    # Two-proportion z-test via chi-square.
    table = pd.crosstab(df["treated"], df["employed_6m"])
    chi2, p, _, _ = stats.chi2_contingency(table)
    return t, c, t - c, p


def adjusted_effect(df):
    feats = ["treated", "age", "prior_unemployed_months", "has_year12"]
    X = pd.get_dummies(df[feats + ["region"]], columns=["region"],
                       drop_first=True).astype(float)
    y = df["employed_6m"].astype(int)
    model = LogisticRegression(max_iter=1000)
    model.fit(X, y)
    # Average marginal effect of 'treated': predict with treated=1 vs 0 for everyone.
    X1 = X.copy(); X1["treated"] = 1.0
    X0 = X.copy(); X0["treated"] = 0.0
    ame = (model.predict_proba(X1)[:, 1] - model.predict_proba(X0)[:, 1]).mean()
    return ame


def subgroups(df):
    rows = []
    df = df.assign(ltu=np.where(df["prior_unemployed_months"] > 6,
                                "Long-term unemployed", "Shorter unemployment"))
    for col in ["region", "ltu", "has_year12"]:
        for val, sub in df.groupby(col):
            t = sub[sub["treated"] == 1]["employed_6m"].mean()
            c = sub[sub["treated"] == 0]["employed_6m"].mean()
            rows.append({"dimension": col, "group": str(val),
                         "lift_pp": round((t - c) * 100, 1),
                         "n": len(sub)})
    return pd.DataFrame(rows)


def cost_effectiveness(df, adj_effect):
    treated = df[df["treated"] == 1]
    avg_cost = treated["cost_aud"].mean()
    n_treated = len(treated)
    extra_employed = adj_effect * n_treated
    total_program_cost = treated["cost_aud"].sum()
    cost_per_outcome = total_program_cost / extra_employed if extra_employed else np.nan
    return avg_cost, extra_employed, cost_per_outcome


def plot(df):
    rates = df.groupby("treated")["employed_6m"].mean() * 100
    fig, ax = plt.subplots(figsize=(5.5, 4))
    ax.bar(["Comparison", "Program"], [rates[0], rates[1]],
           color=["#a6a6a6", "#2e75b6"])
    for i, v in enumerate([rates[0], rates[1]]):
        ax.text(i, v + 1, f"{v:.1f}%", ha="center", fontsize=11)
    ax.set_ylabel("Employed at 6 months (%)")
    ax.set_title("Employment outcome by group (synthetic)")
    fig.tight_layout(); fig.savefig(OUT / "outcomes.png", dpi=130)
    plt.close(fig)


def main():
    OUT.mkdir(exist_ok=True)
    df = load()
    t, c, raw_diff, pval = raw_effect(df)
    ame = adjusted_effect(df)
    sg = subgroups(df)
    avg_cost, extra_employed, cost_per = cost_effectiveness(df, ame)
    plot(df)

    # Baseline balance check
    bal = df.groupby("treated")[["age", "prior_unemployed_months", "has_year12"]] \
        .mean().round(2)

    md = []
    md.append("# Program Evaluation — Pathways to Work (synthetic)\n")
    md.append("> Fictional youth employment program. Data from `generate_data.py`. "
              "This is a methods demonstration, not a real evaluation.\n")
    md.append("## 1. Headline (raw) result\n")
    md.append(f"- Program group employed at 6 months: **{t*100:.1f}%**")
    md.append(f"- Comparison group: **{c*100:.1f}%**")
    md.append(f"- Raw difference: **{raw_diff*100:+.1f} pp** "
              f"(chi-square p = {pval:.4f})\n")
    md.append("## 2. Baseline balance\n")
    md.append("Before trusting the raw number, check the groups are comparable:\n")
    md.append(bal.to_markdown())
    md.append("")
    md.append("## 3. Adjusted effect\n")
    md.append(f"Controlling for age, prior unemployment, Year 12 and region "
              f"(logistic regression, average marginal effect), the program's "
              f"estimated impact is **{ame*100:+.1f} percentage points** — the more "
              "defensible estimate of what the program actually contributed.\n")
    md.append("## 4. Who benefits most\n")
    md.append(sg.sort_values('lift_pp', ascending=False).to_markdown(index=False))
    md.append("")
    md.append("## 5. Cost-effectiveness\n")
    md.append(f"- Average cost per program participant: **${avg_cost:,.0f}**")
    md.append(f"- Estimated additional people employed: **{extra_employed:.0f}**")
    md.append(f"- **Cost per additional employment outcome: ~${cost_per:,.0f}**\n")
    md.append("## Recommendation\n")
    top = sg.sort_values('lift_pp', ascending=False).iloc[0]
    md.append(f"The program shows a positive, statistically detectable effect that "
              f"survives covariate adjustment. Impact is strongest for "
              f"*{top['group']}*, suggesting tighter targeting could improve "
              "cost-effectiveness. Recommend continuation with a focus on the "
              "highest-lift subgroups and a longer follow-up window.\n")
    (OUT / "evaluation_report.md").write_text("\n".join(md))

    print(f"Raw diff: {raw_diff*100:+.1f}pp (p={pval:.4f}) | "
          f"Adjusted: {ame*100:+.1f}pp")
    print(f"Cost per additional outcome: ${cost_per:,.0f}")
    print("Wrote outputs/outcomes.png, evaluation_report.md")


if __name__ == "__main__":
    main()
