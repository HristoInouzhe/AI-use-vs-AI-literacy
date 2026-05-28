#!/usr/bin/env python3
"""
Reproduces every numerical result and figure used in
"AI Receptivity or AI Adoption Breadth? A Tool-Specific Reanalysis of the
Lower-Literacy / Higher-Usage Link" by carrying out four analyses:

  * Block A: Pooled five-tool replication.
  * Block B: Text-AI only.
  * Block C: Non-text AI only (image, productivity, website, health app).
  * Block D: Non-text AI only with binary adoption threshold y>1.

All four blocks call the same fitting routines from the project's
`tully_ai_literacy_robustness.py` library: OLS on participant averages,
binary logit on item-level data, ordered (proportional-odds) logit, and
multinomial logit. Item-level models include task fixed effects.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm

# Make the project's robustness library importable.
PROJECT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_DIR))
import statsmodels.formula.api as smf

from tully_ai_literacy_robustness import (  # noqa: E402
    build_long,
    fit_binary_logit,
    fit_multinomial_logit,
    fit_ols_average,
    fit_ordered_logit,
    make_exog,
    predicted_probabilities_ordered,
    read_table,
    zscore,
)
from statsmodels.miscmodels.ordinal_model import OrderedModel  # noqa: E402

DATA_PATH = PROJECT_DIR / "S3_data.xlsx"
FIG_DIR = PROJECT_DIR / "figures"
FIG_DIR.mkdir(exist_ok=True)

LITERACY = "SC0"
DEMOGRAPHIC_COVARS = ["Age", "Income", "GenKnow", "Autonomy", "Gender_dummy_1"]
TABLE4_COVARS = ["TRI", "GenKnow", "Autonomy", "Gender_dummy_1"]
COVARS = DEMOGRAPHIC_COVARS
NONTEXT = ["AI_image", "AI_productivity", "AI_website", "AI_healthapp"]
ALL5 = NONTEXT + ["AI_text"]


def filtered_data(df: pd.DataFrame, covariates: list[str]) -> pd.DataFrame:
    """Use the original Study 3 inclusion flag and complete controls."""
    dat = df[df["filter_$"] == 1].copy()
    return dat.dropna(subset=covariates)


def run_block(
    name: str,
    outcome_cols: list[str],
    threshold: float | None = None,
    covariates: list[str] | None = None,
) -> None:
    covariates = covariates or COVARS
    print("\n" + "#" * 88)
    print(f"BLOCK: {name}")
    print("#" * 88)
    df = filtered_data(read_table(DATA_PATH), covariates)
    long = build_long(df, LITERACY, outcome_cols, id_col=None, covariates=covariates)
    id_col = "__row_id__"
    print(f"N participants: {long[id_col].nunique()} | N item-level rows: {len(long)}")
    fit_ols_average(long, id_col=id_col, literacy_col=LITERACY, covariates=covariates)
    fit_binary_logit(long, covariates=covariates, threshold=threshold)
    fit_ordered_logit(long, covariates=covariates)
    fit_multinomial_logit(long, covariates=covariates)
    predicted_probabilities_ordered(long, covariates=covariates)


def effect_rows(
    df: pd.DataFrame,
    spec: str,
    covariates: list[str],
    group_label: str,
    outcome_cols: list[str],
) -> list[dict[str, float | str | int]]:
    """Return the AI-literacy coefficient for compact result tables."""
    long = build_long(
        filtered_data(df, covariates),
        LITERACY,
        outcome_cols,
        id_col=None,
        covariates=covariates,
    )
    rows: list[dict[str, float | str | int]] = []

    # OLS on participant-level average (matches original Study 3 specification).
    wide_avg = (
        long.groupby("__row_id__")
        .agg(y_avg=("y", "mean"), literacy=(LITERACY, "first"),
             **{c: (c, "first") for c in covariates})
        .reset_index()
    )
    wide_avg["z_literacy"] = zscore(wide_avg["literacy"])
    rhs_parts = ["z_literacy"]
    for c in covariates:
        if pd.api.types.is_numeric_dtype(wide_avg[c]):
            wide_avg[f"z_{c}"] = zscore(wide_avg[c])
            rhs_parts.append(f"z_{c}")
        else:
            rhs_parts.append(f"C({c})")
    ols_res = smf.ols("y_avg ~ " + " + ".join(rhs_parts), data=wide_avg).fit(cov_type="HC3")
    rows.append({
        "spec": spec,
        "group": group_label,
        "model": "OLS",
        "n_participants": len(wide_avg),
        "n_rows": len(wide_avg),
        "beta": float(ols_res.params["z_literacy"]),
        "se": float(ols_res.bse["z_literacy"]),
        "p": float(ols_res.pvalues["z_literacy"]),
        "or": np.nan,
    })

    exog = make_exog(long, covariates=covariates, task_fe=True)
    ordered = OrderedModel(long["y"].astype(int), exog, distr="logit").fit(
        method="bfgs", maxiter=1000, disp=False
    )
    rows.append({
        "spec": spec,
        "group": group_label,
        "model": "Ordered logit",
        "n_participants": long["__row_id__"].nunique(),
        "n_rows": len(long),
        "beta": float(ordered.params["z_literacy"]),
        "se": float(ordered.bse["z_literacy"]),
        "p": float(ordered.pvalues["z_literacy"]),
        "or": np.nan,
    })

    for threshold, model_label in [(3, "Binary logit (Y > 3)"), (1, "Binary adoption (Y > 1)")]:
        dat = long.copy()
        dat["y_bin"] = (dat["y"] > threshold).astype(int)
        exog_bin = sm.add_constant(make_exog(dat, covariates=covariates, task_fe=True), has_constant="add")
        binary = sm.GLM(dat["y_bin"], exog_bin, family=sm.families.Binomial()).fit(cov_type="HC3")
        rows.append({
            "spec": spec,
            "group": group_label,
            "model": model_label,
            "n_participants": long["__row_id__"].nunique(),
            "n_rows": len(long),
            "beta": float(binary.params["z_literacy"]),
            "se": float(binary.bse["z_literacy"]),
            "p": float(binary.pvalues["z_literacy"]),
            "or": float(np.exp(binary.params["z_literacy"])),
        })

    return rows


def save_predicted_probs() -> None:
    """Compute and save ordered-logit predicted P(y=1, Never) over a literacy grid.

    Covers the two models cited in the paper text (lines 317-322):
      - Text AI only (demographic-adjusted)
      - Non-text AI (demographic-adjusted)
    Grid: z_literacy from -2 to +2 in 0.25 steps.
    Covariates held at zero (i.e., at their sample means after z-scoring).
    """
    df = filtered_data(read_table(DATA_PATH), COVARS)
    grid = np.arange(-2.0, 2.01, 0.25)
    all_rows = []

    for label, cols in [("Text only", ["AI_text"]), ("Non-text only", NONTEXT)]:
        long = build_long(df, LITERACY, cols, id_col=None, covariates=COVARS)
        exog = make_exog(long, covariates=COVARS, task_fe=True)
        y = long["y"].astype(int)
        res = OrderedModel(y, exog, distr="logit").fit(method="bfgs", maxiter=1000, disp=False)
        base = pd.DataFrame(np.zeros((len(grid), exog.shape[1])), columns=exog.columns)
        base["z_literacy"] = grid
        pred = res.model.predict(res.params, exog=base)
        cats = sorted(y.unique())
        for i, z in enumerate(grid):
            row = {"group": label, "z_literacy": round(float(z), 2)}
            for j, cat in enumerate(cats):
                row[f"P(y={cat})"] = float(pred[i, j])
            all_rows.append(row)

    pred_df = pd.DataFrame(all_rows)
    out = PROJECT_DIR / "predicted_probs.csv"
    pred_df.to_csv(out, index=False)
    print(f"Saved predicted probabilities to {out}")

    # Print the paper-cited anchor values (z = -2 and z = +2).
    print("\nPaper-cited predicted P(y=1, Never) anchor values:")
    for label in ["Text only", "Non-text only"]:
        sub = pred_df[pred_df["group"] == label]
        p_lo = sub.loc[sub["z_literacy"] == -2.0, "P(y=1)"].values[0]
        p_hi = sub.loc[sub["z_literacy"] == 2.0, "P(y=1)"].values[0]
        print(f"  {label}: z=-2 → {p_lo:.3f}, z=+2 → {p_hi:.3f}")


def save_descriptive_stats() -> None:
    """Compute and save usage-distribution descriptive stats cited in paper text."""
    df = filtered_data(read_table(DATA_PATH), COVARS)
    rows = []
    for col in ALL5:
        counts = df[col].dropna().astype(int).value_counts().sort_index()
        total = counts.sum()
        for cat, cnt in counts.items():
            rows.append({"tool": col, "category": int(cat), "count": int(cnt),
                         "share": float(cnt / total)})
    desc_df = pd.DataFrame(rows)
    out = PROJECT_DIR / "descriptive_stats.csv"
    desc_df.to_csv(out, index=False)
    print(f"Saved descriptive statistics to {out}")

    # Print the paper-cited summary values.
    print("\nPaper-cited descriptive values:")
    text_used = (df["AI_text"] > 1).sum()
    print(f"  Text AI used at least occasionally (Y>1): {text_used}/{len(df)} = {text_used/len(df):.1%}")
    for col in NONTEXT:
        never = (df[col] == 1).sum()
        print(f"  {col} Never (Y=1): {never}/{len(df)} = {never/len(df):.1%}")


def write_result_tables() -> None:
    """Write primary and original-Table-4 robustness coefficient tables."""
    df = read_table(DATA_PATH)
    groups = [
        ("Pooled (5 tools)", ALL5),
        ("Text only", ["AI_text"]),
        ("Non-text only", NONTEXT),
    ]
    rows = []
    for spec, covariates in [
        ("Demographic-adjusted", DEMOGRAPHIC_COVARS),
        ("Original Table 4 covariates", TABLE4_COVARS),
    ]:
        for group_label, cols in groups:
            rows.extend(effect_rows(df, spec, covariates, group_label, cols))
    result_df = pd.DataFrame(rows)
    result_df.to_csv(PROJECT_DIR / "result_table.csv", index=False)
    print(result_df.round({"beta": 3, "se": 3, "p": 4, "or": 3}).to_string(index=False))


def make_predicted_probability_figure() -> None:
    """Figure 1: P(y=1) over literacy grid for text vs non-text."""
    df = filtered_data(read_table(DATA_PATH), COVARS)
    grid = np.linspace(-2.0, 2.0, 17)
    fig, ax = plt.subplots(figsize=(6.2, 4.2))

    for label, cols, color, marker in [
        ("Text AI (writing assistants)", ["AI_text"], "#1f77b4", "o"),
        ("Non-text AI tools", NONTEXT, "#d62728", "s"),
    ]:
        long = build_long(df, LITERACY, cols, id_col=None, covariates=COVARS)
        exog = make_exog(long, covariates=COVARS, task_fe=True)
        y = long["y"].astype(int)
        res = OrderedModel(y, exog, distr="logit").fit(method="bfgs", maxiter=1000, disp=False)
        base = pd.DataFrame(np.zeros((len(grid), exog.shape[1])), columns=exog.columns)
        base["z_literacy"] = grid
        pred = res.model.predict(res.params, exog=base)
        # P(y=1) is the first column (lowest category).
        p_never = pred[:, 0]
        ax.plot(grid, p_never, marker=marker, color=color, linewidth=2, markersize=4,
                label=label)

    ax.set_xlabel("AI literacy (standardized)")
    ax.set_ylabel(r"Predicted $\Pr(\text{Never used})$")
    ax.set_ylim(0.0, 1.0)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper left", frameon=True)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "predicted_prob_never.pdf", dpi=300, bbox_inches="tight")
    fig.savefig(FIG_DIR / "predicted_prob_never.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {FIG_DIR / 'predicted_prob_never.pdf'}")


def make_coefficient_comparison_figure() -> None:
    """Figure 2: AI-literacy coefficient across tool groupings and model families."""
    df = filtered_data(read_table(DATA_PATH), COVARS)

    rows = []
    for group_label, cols in [
        ("Pooled (5 tools)", ALL5),
        ("Non-text only", NONTEXT),
        ("Text only", ["AI_text"]),
    ]:
        long = build_long(df, LITERACY, cols, id_col=None, covariates=COVARS)

        # Ordered logit
        exog = make_exog(long, covariates=COVARS, task_fe=True)
        y = long["y"].astype(int)
        res = OrderedModel(y, exog, distr="logit").fit(method="bfgs", maxiter=1000, disp=False)
        beta = float(res.params["z_literacy"])
        se = float(res.bse["z_literacy"])
        rows.append({"group": group_label, "model": "Ordered logit", "beta": beta, "se": se})

        # Binary logit at midpoint (y>3) on item-level data
        threshold = (long["y"].min() + long["y"].max()) / 2
        dat = long.copy()
        dat["y_bin"] = (dat["y"] > threshold).astype(int)
        exog_b = make_exog(dat, covariates=COVARS, task_fe=True)
        exog_b = sm.add_constant(exog_b, has_constant="add")
        m = sm.GLM(dat["y_bin"], exog_b, family=sm.families.Binomial()).fit(cov_type="HC3")
        rows.append({"group": group_label, "model": "Binary logit (y>3)",
                     "beta": float(m.params["z_literacy"]),
                     "se": float(m.bse["z_literacy"])})

        # Binary adoption (y>1) on item-level data
        dat2 = long.copy()
        dat2["y_bin"] = (dat2["y"] > 1).astype(int)
        exog_a = make_exog(dat2, covariates=COVARS, task_fe=True)
        exog_a = sm.add_constant(exog_a, has_constant="add")
        m2 = sm.GLM(dat2["y_bin"], exog_a, family=sm.families.Binomial()).fit(cov_type="HC3")
        rows.append({"group": group_label, "model": "Binary adoption (y>1)",
                     "beta": float(m2.params["z_literacy"]),
                     "se": float(m2.bse["z_literacy"])})

    coef_df = pd.DataFrame(rows)
    coef_df.to_csv(FIG_DIR.parent / "coefficient_table.csv", index=False)
    print(coef_df.round(3).to_string(index=False))

    # Forest-style plot
    fig, ax = plt.subplots(figsize=(7.0, 4.4))
    groups = ["Pooled (5 tools)", "Non-text only", "Text only"]
    models = ["Ordered logit", "Binary logit (y>3)", "Binary adoption (y>1)"]
    colors = {"Ordered logit": "#1f77b4",
              "Binary logit (y>3)": "#2ca02c",
              "Binary adoption (y>1)": "#d62728"}
    y_positions = np.arange(len(groups))
    offsets = {m: (i - 1) * 0.22 for i, m in enumerate(models)}

    for model in models:
        sub = coef_df[coef_df["model"] == model]
        for _, row in sub.iterrows():
            ypos = y_positions[groups.index(row["group"])] + offsets[model]
            ci_lo = row["beta"] - 1.96 * row["se"]
            ci_hi = row["beta"] + 1.96 * row["se"]
            ax.errorbar(row["beta"], ypos, xerr=[[row["beta"] - ci_lo], [ci_hi - row["beta"]]],
                        fmt="o", color=colors[model], capsize=3,
                        label=model if row["group"] == "Pooled (5 tools)" else None)
    ax.axvline(0, color="black", linewidth=0.8, linestyle="--")
    ax.set_yticks(y_positions)
    ax.set_yticklabels(groups)
    ax.set_xlabel("Coefficient on +1 SD AI literacy (95% CI)")
    ax.set_title("AI-literacy effect by tool group and model family")
    ax.legend(loc="lower right", frameon=True)
    ax.grid(True, axis="x", alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "coefficient_comparison.pdf", dpi=300, bbox_inches="tight")
    fig.savefig(FIG_DIR / "coefficient_comparison.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {FIG_DIR / 'coefficient_comparison.pdf'}")


def make_usage_distribution_figure() -> None:
    """Descriptive figure: distribution of each AI tool's reported usage."""
    df = filtered_data(read_table(DATA_PATH), COVARS)
    labels = {
        "AI_image": "Image generators\n(e.g. DALL-E)",
        "AI_productivity": "Productivity tools\n(e.g. Zapier)",
        "AI_website": "Website/design\n(e.g. Canva)",
        "AI_healthapp": "Health apps\n(e.g. Headspace)",
        "AI_text": "Writing assistants\n(e.g. ChatGPT)",
    }
    fig, ax = plt.subplots(figsize=(7.5, 4.0))
    width = 0.16
    x_cats = np.arange(1, 6, dtype=float)
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#9467bd", "#d62728"]
    for i, col in enumerate(ALL5):
        counts = df[col].dropna().astype(int).value_counts().reindex(x_cats, fill_value=0)
        share = (counts / counts.sum()).to_numpy(dtype=float)
        ax.bar(x_cats + (i - 2) * width, share, width=width,
               color=colors[i], label=labels[col])
    ax.set_xticks(x_cats)
    ax.set_xticklabels(["1\nNever", "2\nOnce/twice", "3\nOccasion.", "4\nFreq.", "5\nWeekly"])
    ax.set_ylabel("Share of respondents")
    ax.set_title("Reported usage frequency by AI tool category (N = 401)")
    ax.legend(loc="upper right", frameon=True, fontsize=8)
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "usage_distribution.pdf", dpi=300, bbox_inches="tight")
    fig.savefig(FIG_DIR / "usage_distribution.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {FIG_DIR / 'usage_distribution.pdf'}")


if __name__ == "__main__":
    # All four estimation blocks.
    run_block("A. Pooled 5-tool replication", ALL5)
    run_block("B. Text AI only", ["AI_text"])
    run_block("C. Non-text AI only", NONTEXT)
    run_block("D. Non-text AI only, adoption threshold y>1", NONTEXT, threshold=1)

    # Save all numerical results (including OLS) to result_table.csv.
    print("\n--- Saving coefficient tables ---")
    write_result_tables()

    # Save predicted probabilities (paper text lines 317-322).
    print("\n--- Saving predicted probabilities ---")
    save_predicted_probs()

    # Save descriptive statistics (two-thirds and 65-78% claims).
    print("\n--- Saving descriptive statistics ---")
    save_descriptive_stats()

    # Figures.
    print("\n--- Generating figures ---")
    try:
        make_usage_distribution_figure()
        make_predicted_probability_figure()
        make_coefficient_comparison_figure()
    except Exception as exc:
        print(f"Figure generation skipped: {exc}")
