# Tool-Specific Reanalysis of Tully, Longoni & Appel (2025) — Study 3

> **"AI Receptivity or AI Adoption Breadth? A Tool-Specific Reanalysis of the
> Lower-Literacy/Higher-Usage Link"**
>
> Anonymous (Replication and robustness reanalysis)  
> Target venue: *Marketing Letters*, Replication Corner

## Repository contents

| File | Description |
|---|---|
| `run_experiments.py` | Main script — runs all estimation blocks, writes all output CSVs, and regenerates figures |
| `tully_ai_literacy_robustness.py` | Model library: OLS, binary logit, ordered logit, multinomial logit |
| `reanalysis_notebook.ipynb` | Executed Jupyter notebook reproducing tables and figures |
| `S3_data.xlsx` | Study 3 public data (also available at [ResearchBox #1491](https://researchbox.org/1491)) |
| `references.bib` | 18 bibliographic entries with DOIs |
| `result_table.csv` | All reported coefficients (OLS, ordered logit, binary logit) for both covariate specifications |
| `predicted_probs.csv` | Ordered-logit predicted P(y = 1, "Never") over z = −2 to +2 for text and non-text models |
| `descriptive_stats.csv` | Usage-frequency distributions by AI tool category |

The compiled PDF, LaTeX source, figures, ResearchBox materials, and the original
Tully et al. paper are excluded from this repository (see `.gitignore`) and kept
only locally.

## How to re-run the analyses

### Environment

The analyses require Python ≥ 3.10 with compatible versions of:
`pandas`, `numpy`, `statsmodels`, `openpyxl`, `matplotlib`.

A known-working combination (used to generate all output files):
`numpy 2.0.1`, `pandas 2.3.2`, `statsmodels 0.14.5`, `matplotlib 3.7.1`.

```bash
pip install "numpy>=2.0,<2.1" pandas statsmodels openpyxl matplotlib
```

### Run all experiments

```bash
python run_experiments.py
```

This runs four estimation blocks (pooled 5-tool, text-only, non-text, non-text
adoption), writes `result_table.csv`, `predicted_probs.csv`, and
`descriptive_stats.csv`, and regenerates the figures in `figures/`.

### Interactive exploration

```bash
jupyter notebook reanalysis_notebook.ipynb
```

## Headline results

All numbers are reproduced from the public Study 3 data.
Primary specification: demographic-adjusted (Age, Income, GenKnow, Autonomy,
male-gender indicator). Robustness: original Table 4 covariates (TRI, GenKnow,
Autonomy, male-gender indicator; N = 379 due to missing TRI values).

| Outcome group | Model | β (per +1 SD AI literacy) | *p* |
|---|---|---:|---:|
| Pooled (5 tools) | Ordered logit, demographic-adjusted | −0.307 | < .001 |
| Text only | Ordered logit, demographic-adjusted | −0.090 | .387 |
| Non-text only | Ordered logit, demographic-adjusted | −0.377 | < .001 |
| Non-text only | Binary adoption (Y > 1), demographic-adjusted | −0.388 (OR = 0.68) | < .001 |
| Text only | Ordered logit, original Table 4 covariates | −0.290 | .010 |
| Non-text only | Ordered logit, original Table 4 covariates | −0.502 | < .001 |

Predicted probability of "Never used" for non-text AI rises from **0.50** at
z = −2 to **0.82** at z = +2. The corresponding text-AI curve rises only from
**0.27** to **0.35**.

## Data source

Study 3 data are publicly available from the original authors at
[ResearchBox #1491](https://researchbox.org/1491).
The `S3_data.xlsx` file in this repository is the unmodified Study 3 data file
from that ResearchBox.
