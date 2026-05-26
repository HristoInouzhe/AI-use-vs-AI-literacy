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

# Make the project's robustness library importable.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tully_ai_literacy_robustness import (  # noqa: E402
    build_long,
    fit_binary_logit,
    fit_multinomial_logit,
    fit_ols_average,
    fit_ordered_logit,
    make_exog,
    predicted_probabilities_ordered,
    read_table,
)
from statsmodels.miscmodels.ordinal_model import OrderedModel  # noqa: E402

DATA_PATH = Path(__file__).resolve().parent.parent / "S3_data.xlsx"
FIG_DIR = Path(__file__).resolve().parent / "figures"
FIG_DIR.mkdir(exist_ok=True)

LITERACY = "SC0"
COVARS = ["Age", "Income", "GenKnow", "Autonomy", "Gender"]
NONTEXT = ["AI_image", "AI_productivity", "AI_website", "AI_healthapp"]
ALL5 = NONTEXT + ["AI_text"]


def run_block(name: str, outcome_cols: list[str], threshold: float | None = None) -> None:
    print("\n" + "#" * 88)
    print(f"BLOCK: {name}")
    print("#" * 88)
    df = read_table(DATA_PATH)
    long = build_long(df, LITERACY, outcome_cols, id_col=None, covariates=COVARS)
    id_col = "__row_id__"
    print(f"N participants: {long[id_col].nunique()} | N item-level rows: {len(long)}")
    fit_ols_average(long, id_col=id_col, literacy_col=LITERACY, covariates=COVARS)
    fit_binary_logit(long, covariates=COVARS, threshold=threshold)
    fit_ordered_logit(long, covariates=COVARS)
    fit_multinomial_logit(long, covariates=COVARS)
    predicted_probabilities_ordered(long, covariates=COVARS)


def make_predicted_probability_figure() -> None:
    """Figure 1: P(y=1) over literacy grid for text vs non-text."""
    df = read_table(DATA_PATH)
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
    df = read_table(DATA_PATH)

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
        import statsmodels.api as sm
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
    df = read_table(DATA_PATH)
    labels = {
        "AI_image": "Image generators\n(e.g. DALL-E)",
        "AI_productivity": "Productivity tools\n(e.g. Zapier)",
        "AI_website": "Website/design\n(e.g. Canva)",
        "AI_healthapp": "Health apps\n(e.g. Headspace)",
        "AI_text": "Writing assistants\n(e.g. ChatGPT)",
    }
    fig, ax = plt.subplots(figsize=(7.5, 4.0))
    width = 0.16
    x_cats = np.arange(1, 6)
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#9467bd", "#d62728"]
    for i, col in enumerate(ALL5):
        counts = df[col].dropna().astype(int).value_counts().reindex(x_cats, fill_value=0)
        share = counts / counts.sum()
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

    # Figures.
    print("\n--- Generating figures ---")
    make_usage_distribution_figure()
    make_predicted_probability_figure()
    make_coefficient_comparison_figure()
