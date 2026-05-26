# Tool-Specific Reanalysis of Tully, Longoni & Appel (2025) — Study 3

This bundle contains the manuscript, the bibliography, the executed notebook,
and the underlying scripts and figures for the paper:

> **"AI Receptivity or AI Adoption Breadth? A Tool-Specific Reanalysis of the
> Lower-Literacy/Higher-Usage Link"**

## Contents

- `paper.tex` — main LaTeX manuscript (uses `natbib` with `plainnat` style).
- `paper.pdf` — compiled PDF, 11 pages.
- `references.bib` — 18 verified bibliographic entries with DOIs.
- `reanalysis_notebook.ipynb` — fully executed Jupyter notebook reproducing
  every numerical result and figure in the paper, organised by paper section.
- `run_experiments.py` — non-interactive script that runs all four estimation
  blocks (pooled 5-tool, text-only, non-text, non-text adoption) and writes
  the three figures.
- `tully_ai_literacy_robustness.py` — original project library with the
  four estimation routines (kept here so the notebook is self-contained).
- `S3_data.xlsx` — the Study 3 data file used.
- `figures/` — final figures in PDF and PNG.
- `coefficient_table.csv` — long-form coefficient table used to draw Figure 3.

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

## Target venues

The manuscript is written at ~3,500 words plus tables and figures, fitting the
short-format expectations of *Marketing Letters* and *Journal of Marketing
Analytics*. Both journals accept replication and methodological notes of this
length.

## Headline results (all reproduced from the data)

| Outcome group | Model | Coef. (per +1 SD AI literacy) | p |
|---|---|---:|---:|
| Pooled (5 tools) | Ordered logit | −0.306 | < .001 |
| Text only | Ordered logit | −0.097 | .357 |
| Non-text only | Ordered logit | −0.376 | < .001 |
| Non-text only | Binary adoption (Y > 1) | −0.385 (OR = 0.68) | < .001 |

Predicted probability of "Never used" for non-text AI rises from **0.50** at
z = −2 to **0.82** at z = +2. The corresponding text-AI curve rises only from
**0.27** to **0.36**.
