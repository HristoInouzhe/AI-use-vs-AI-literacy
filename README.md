# Tool-Specific Reanalysis of Tully, Longoni & Appel (2025) — Study 3

This bundle contains the manuscript, the bibliography, the executed notebook,
and the underlying scripts and figures for the paper:

> **"AI Receptivity or AI Adoption Breadth? A Tool-Specific Reanalysis of the
> Lower-Literacy/Higher-Usage Link"**

## Contents

- `paper.tex` — main LaTeX manuscript (uses `natbib` with `plainnat` style).
- `paper.pdf` — compiled PDF, 11 pages.
- `references.bib` — 18 verified bibliographic entries with DOIs.
- `reanalysis_notebook.ipynb` — Jupyter notebook reproducing the numerical
  analyses and figures in the paper, organised by paper section.
- `run_experiments.py` — non-interactive script that runs all four estimation
  blocks (pooled 5-tool, text-only, non-text, non-text adoption), writes
  `result_table.csv`, and attempts to regenerate the figures.
- `tully_ai_literacy_robustness.py` — original project library with the
  four estimation routines (kept here so the notebook is self-contained).
- `S3_data.xlsx` — the Study 3 data file used.
- `figures/` — final figures in PDF and PNG.
- `result_table.csv` — long-form coefficient table for the demographic-adjusted
  primary models and original-Table-4 robustness models.

## How to recompile the PDF

```
pdflatex paper.tex
bibtex paper
pdflatex paper.tex
pdflatex paper.tex
```

Requires `texlive-latex-recommended`, `texlive-latex-extra`,
`texlive-fonts-recommended`, and `lmodern`.

## How to re-run the analyses

```
pip install pandas numpy statsmodels openpyxl matplotlib
python run_experiments.py
# or, interactively:
jupyter notebook reanalysis_notebook.ipynb
```

The current local `TFG_env` environment runs the statistical models and writes
`result_table.csv`. Its Matplotlib/Numpy combination is incompatible for figure
export, so figure regeneration may require a fresh environment with mutually
compatible versions.

## Target venues

The manuscript is written to fit the short-format expectations of *Marketing
Letters*. The main text now uses three display items: one primary results
table, one predicted-probability figure, and one robustness table.

## Headline results (all reproduced from the data)

| Outcome group | Model | Coef. (per +1 SD AI literacy) | p |
|---|---|---:|---:|
| Pooled (5 tools) | Ordered logit, demographic-adjusted | −0.307 | < .001 |
| Text only | Ordered logit, demographic-adjusted | −0.090 | .387 |
| Non-text only | Ordered logit, demographic-adjusted | −0.377 | < .001 |
| Non-text only | Binary adoption (Y > 1), demographic-adjusted | −0.388 (OR = 0.68) | < .001 |
| Text only | Ordered logit, original Table 4 covariates | −0.290 | .010 |
| Non-text only | Ordered logit, original Table 4 covariates | −0.502 | < .001 |

Predicted probability of "Never used" for non-text AI rises from **0.50** at
z = −2 to **0.82** at z = +2. The corresponding text-AI curve rises only from
**0.27** to **0.36**.
