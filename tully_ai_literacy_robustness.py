#!/usr/bin/env python3
"""
Robustness checks for Tully, Longoni & Appel (2025), ResearchBox #1491.

Goal
----
The paper often regresses averaged Likert/ordinal responses on AI literacy.
This script fits a few alternative "basic" models on the item-level responses:

1. OLS on the averaged score, close to the paper's main summaries.
2. Binary logit after thresholding the ordinal response.
3. Ordered logit / proportional-odds model on the item-level response.
4. Multinomial logit on the item-level response, treating categories as nominal.

Why both ordinal and multinomial?
---------------------------------
For 1-5 or 1-7 preference/use scales, an ordered model is usually more natural
than a fully multinomial model. Multinomial logit is useful as a robustness check
because it avoids imposing proportional odds and equal spacing, but it also throws
away the ordinal structure.

How to use
----------
1. Install dependencies:
   pip install pandas numpy statsmodels openpyxl requests scipy

2. Run:
   python tully_ai_literacy_robustness.py --download

   If the direct ResearchBox zip URL fails, manually download the files from:
   https://researchbox.org/1491
   and unzip them into ./researchbox_1491/

3. Inspect the printed columns:
   python tully_ai_literacy_robustness.py --root ./researchbox_1491 --inspect

4. Run a study by specifying the file, literacy column, and outcome columns:
   python tully_ai_literacy_robustness.py \
       --file ./researchbox_1491/S2_Data.xlsx \
       --literacy-col "AI_literacy" \
       --outcome-cols "assignment_1,assignment_2,assignment_3,assignment_4" \
       --id-col "ResponseId"

   For Study 6 or Study 7, pass all task columns as outcome-cols.

Notes
-----
- Column names in public repositories often differ from the paper's notation.
  The script is intentionally explicit: inspect first, then pass the columns.
- statsmodels' OrderedModel does not provide a full mixed-effects ordinal model.
  Here task fixed effects are included when multiple items/tasks are supplied.
  For publication-level robustness with random effects, use R packages such as
  ordinal::clmm or brms::brm(family = cumulative()).
"""

from __future__ import annotations

import argparse
import re
import sys
import zipfile
from pathlib import Path
from typing import Iterable, Optional

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.miscmodels.ordinal_model import OrderedModel


BOX_ZIP_URL = "https://s3.wasabisys.com/zipballs.researchbox.org/ResearchBox_1491.zip"


# ---------------------------------------------------------------------
# Download / file handling
# ---------------------------------------------------------------------

def download_zip(out_zip: Path, url: str = BOX_ZIP_URL) -> Path:
    """Download ResearchBox #1491 zip."""
    import requests

    out_zip.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {url}")
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        done = 0
        with out_zip.open("wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
                    done += len(chunk)
                    if total:
                        pct = 100 * done / total
                        print(f"\r  {done/1e6:.1f} MB / {total/1e6:.1f} MB ({pct:.1f}%)", end="")
                    else:
                        print(f"\r  {done/1e6:.1f} MB", end="")
    print("\nDownload complete.")
    return out_zip


def unzip(zip_path: Path, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(out_dir)
    print(f"Extracted to {out_dir}")
    return out_dir


def list_files(root: Path) -> pd.DataFrame:
    rows = []
    for p in root.rglob("*"):
        if p.is_file():
            rows.append({
                "path": str(p),
                "name": p.name,
                "suffix": p.suffix.lower(),
                "size_kb": round(p.stat().st_size / 1024, 1),
            })
    return pd.DataFrame(rows).sort_values(["suffix", "name"])


def read_table(path: Path, sheet: Optional[str] = None) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix in {".xlsx", ".xls"} or path.name.lower().endswith(".xlsx.xls"):
        if sheet is None:
            sheets = pd.read_excel(path, sheet_name=None)
            print(f"Excel sheets in {path.name}: {list(sheets.keys())}")
            # choose first non-empty sheet
            for nm, df in sheets.items():
                if len(df) > 0 and df.shape[1] > 1:
                    print(f"Using sheet: {nm}")
                    return df
            return next(iter(sheets.values()))
        return pd.read_excel(path, sheet_name=sheet)
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".tsv", ".txt"}:
        return pd.read_csv(path, sep="\t")
    raise ValueError(f"Unsupported data format: {path}")


# ---------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------

def split_cols(s: str) -> list[str]:
    return [x.strip() for x in s.split(",") if x.strip()]


def zscore(x: pd.Series) -> pd.Series:
    x = pd.to_numeric(x, errors="coerce")
    return (x - x.mean()) / x.std(ddof=0)


def coerce_ordinal(y: pd.Series) -> pd.Series:
    """Convert common survey encodings to ordered integer categories."""
    if pd.api.types.is_numeric_dtype(y):
        return pd.to_numeric(y, errors="coerce")

    # Try to recover the leading number in strings like "1 = Definitely prefer human"
    extracted = y.astype(str).str.extract(r"^\s*([0-9]+(?:\.[0-9]+)?)")[0]
    out = pd.to_numeric(extracted, errors="coerce")
    if out.notna().mean() > 0.7:
        return out

    # Otherwise encode ordered by sorted unique labels; inspect before trusting.
    cats = pd.Categorical(y)
    return pd.Series(cats.codes + 1, index=y.index).where(~y.isna(), np.nan)


def build_long(
    df: pd.DataFrame,
    literacy_col: str,
    outcome_cols: list[str],
    id_col: Optional[str] = None,
    covariates: Optional[list[str]] = None,
) -> pd.DataFrame:
    covariates = covariates or []

    missing = [c for c in [literacy_col, *outcome_cols, *covariates] if c not in df.columns]
    if missing:
        raise KeyError(f"These columns are not in the dataset: {missing}")

    if id_col is None or id_col not in df.columns:
        id_col = "__row_id__"
        df = df.copy()
        df[id_col] = np.arange(len(df))

    keep = [id_col, literacy_col, *covariates, *outcome_cols]
    wide = df[keep].copy()
    for c in outcome_cols:
        wide[c] = coerce_ordinal(wide[c])

    long = wide.melt(
        id_vars=[id_col, literacy_col, *covariates],
        value_vars=outcome_cols,
        var_name="task",
        value_name="y",
    )
    long = long.dropna(subset=["y", literacy_col]).copy()
    long["y"] = long["y"].astype(int)
    long["z_literacy"] = zscore(long[literacy_col])
    long = long.dropna(subset=["z_literacy"]).copy()
    return long


def make_exog(long: pd.DataFrame, covariates: Optional[list[str]] = None, task_fe: bool = True) -> pd.DataFrame:
    covariates = covariates or []
    parts = [long[["z_literacy"]].astype(float)]

    for c in covariates:
        if pd.api.types.is_numeric_dtype(long[c]):
            parts.append(pd.DataFrame({f"z_{c}": zscore(long[c])}, index=long.index))
        else:
            parts.append(pd.get_dummies(long[c], prefix=c, drop_first=True, dtype=float))

    if task_fe and long["task"].nunique() > 1:
        parts.append(pd.get_dummies(long["task"], prefix="task", drop_first=True, dtype=float))

    exog = pd.concat(parts, axis=1).astype(float)
    # Remove constant-like columns; OrderedModel must not include an intercept.
    nunique = exog.nunique(dropna=True)
    exog = exog.loc[:, nunique > 1]
    return exog


def print_header(title: str) -> None:
    print("\n" + "=" * 88)
    print(title)
    print("=" * 88)


# ---------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------

def fit_ols_average(
    long: pd.DataFrame,
    id_col: str,
    literacy_col: str,
    covariates: Optional[list[str]] = None,
) -> None:
    """OLS on participant-level average response."""
    covariates = covariates or []
    print_header("1) OLS on participant-level average response")

    wide_avg = (
        long.groupby(id_col)
        .agg(y_avg=("y", "mean"), literacy=(literacy_col, "first"), **{c: (c, "first") for c in covariates})
        .reset_index()
    )
    wide_avg["z_literacy"] = zscore(wide_avg["literacy"])

    rhs = ["z_literacy"]
    for c in covariates:
        if pd.api.types.is_numeric_dtype(wide_avg[c]):
            wide_avg[f"z_{c}"] = zscore(wide_avg[c])
            rhs.append(f"z_{c}")
        else:
            rhs.append(f"C({c})")

    formula = "y_avg ~ " + " + ".join(rhs)
    model = smf.ols(formula, data=wide_avg).fit(cov_type="HC3")
    print(model.summary().tables[1])


def fit_binary_logit(
    long: pd.DataFrame,
    covariates: Optional[list[str]] = None,
    threshold: Optional[float] = None,
) -> None:
    """Logit on item-level response after thresholding at the midpoint."""
    covariates = covariates or []
    print_header("2) Binary logit on item-level response, thresholded at scale midpoint")

    if threshold is None:
        threshold = (long["y"].min() + long["y"].max()) / 2
    dat = long.copy()
    dat["y_bin"] = (dat["y"] > threshold).astype(int)

    exog = make_exog(dat, covariates=covariates, task_fe=True)
    exog_const = sm.add_constant(exog, has_constant="add")
    model = sm.GLM(dat["y_bin"], exog_const, family=sm.families.Binomial()).fit(cov_type="HC3")
    print(f"Threshold: y > {threshold:g}")
    print(model.summary().tables[1])

    if "z_literacy" in model.params.index:
        odds_ratio = float(np.exp(model.params["z_literacy"]))
        print(f"\nOdds ratio for +1 SD AI literacy: {odds_ratio:.3f}")


def fit_ordered_logit(
    long: pd.DataFrame,
    covariates: Optional[list[str]] = None,
) -> None:
    """Ordered logit / proportional-odds model."""
    covariates = covariates or []
    print_header("3) Ordered logit / proportional-odds model on item-level response")

    exog = make_exog(long, covariates=covariates, task_fe=True)
    y = long["y"].astype(int)

    model = OrderedModel(y, exog, distr="logit")
    res = model.fit(method="bfgs", maxiter=1000, disp=False)
    print(res.summary())

    if "z_literacy" in res.params.index:
        # In statsmodels OrderedModel, a positive coefficient shifts mass toward higher categories.
        beta = float(res.params["z_literacy"])
        print(f"\nOrdered-logit coefficient for +1 SD AI literacy: {beta:.3f}")
        print("Positive means higher AI literacy predicts higher response categories; negative means lower categories.")


def fit_multinomial_logit(
    long: pd.DataFrame,
    covariates: Optional[list[str]] = None,
) -> None:
    """Nominal multinomial logit on item-level response."""
    covariates = covariates or []
    print_header("4) Multinomial logit on item-level response, treating categories as nominal")

    dat = long.copy()
    cats = sorted(dat["y"].dropna().unique())
    cat_to_code = {cat: i for i, cat in enumerate(cats)}
    dat["y_code"] = dat["y"].map(cat_to_code).astype(int)

    exog = make_exog(dat, covariates=covariates, task_fe=True)
    exog_const = sm.add_constant(exog, has_constant="add")

    model = sm.MNLogit(dat["y_code"], exog_const)
    res = model.fit(method="newton", maxiter=200, disp=False)
    print(res.summary())

    print("\nCategory coding for MNLogit:")
    for k, v in cat_to_code.items():
        print(f"  original y={k} -> code {v}")
    print("The base category is the first code used internally by statsmodels, usually the lowest code.")


def predicted_probabilities_ordered(
    long: pd.DataFrame,
    covariates: Optional[list[str]] = None,
    grid: Optional[list[float]] = None,
) -> None:
    """Simple predictions from ordered model at literacy quantiles, task fixed effects set to zero."""
    covariates = covariates or []
    grid = grid or [-2, -1, 0, 1, 2]

    print_header("5) Ordered-logit predicted category probabilities over AI literacy grid")

    exog = make_exog(long, covariates=covariates, task_fe=True)
    y = long["y"].astype(int)
    model = OrderedModel(y, exog, distr="logit")
    res = model.fit(method="bfgs", maxiter=1000, disp=False)

    base = pd.DataFrame(np.zeros((len(grid), exog.shape[1])), columns=exog.columns)
    base["z_literacy"] = grid
    pred = res.model.predict(res.params, exog=base)
    pred = pd.DataFrame(pred, columns=[f"P(y={c})" for c in sorted(y.unique())])
    pred.insert(0, "z_literacy", grid)
    print(pred.round(3).to_string(index=False))


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def inspect(root: Path) -> None:
    print_header("Files")
    files = list_files(root)
    if files.empty:
        print(f"No files found under {root}")
        return
    print(files.to_string(index=False))

    print_header("Excel/CSV columns")
    for _, row in files.iterrows():
        p = Path(row["path"])
        if p.suffix.lower() in {".xlsx", ".xls", ".csv", ".tsv"} or p.name.lower().endswith(".xlsx.xls"):
            try:
                df = read_table(p)
                print(f"\n{p.name}: shape={df.shape}")
                for i, c in enumerate(df.columns):
                    print(f"  {i:03d}: {c}")
            except Exception as e:
                print(f"\nCould not inspect {p}: {e}")

    print_header("R code model lines")
    for _, row in files.iterrows():
        p = Path(row["path"])
        if p.suffix.lower() == ".r":
            try:
                text = p.read_text(errors="ignore")
                hits = [ln for ln in text.splitlines() if re.search(r"\b(lm|glm|lmer|glmer|clm|polr|multinom|process|mediate)\b", ln, re.I)]
                if hits:
                    print(f"\n{p.name}")
                    for ln in hits[:40]:
                        print("  " + ln[:200])
            except Exception:
                pass


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--download", action="store_true", help="Download and unzip ResearchBox #1491.")
    parser.add_argument("--root", type=Path, default=Path("./researchbox_1491"), help="Folder containing extracted files.")
    parser.add_argument("--zip", type=Path, default=Path("./ResearchBox_1491.zip"), help="Zip path.")
    parser.add_argument("--inspect", action="store_true", help="List files and columns.")
    parser.add_argument("--file", type=Path, help="Dataset file to analyze, e.g. S2_Data.xlsx or S6_Data.xlsx.xls.")
    parser.add_argument("--sheet", type=str, default=None, help="Excel sheet name.")
    parser.add_argument("--literacy-col", type=str, help="AI literacy score column.")
    parser.add_argument("--outcome-cols", type=str, help="Comma-separated ordinal response columns.")
    parser.add_argument("--id-col", type=str, default=None, help="Participant ID column. If omitted, row index is used.")
    parser.add_argument("--covariates", type=str, default="", help="Comma-separated covariate columns.")
    parser.add_argument("--threshold", type=float, default=None, help="Binary threshold; default is scale midpoint.")
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.download:
        try:
            download_zip(args.zip)
            unzip(args.zip, args.root)
        except Exception as e:
            print("\nDownload failed.")
            print(f"Reason: {e}")
            print("Manual fallback: download the box from https://researchbox.org/1491 and unzip it into:")
            print(f"  {args.root.resolve()}")
            return 1

    if args.inspect:
        inspect(args.root)
        return 0

    if not args.file:
        print("No --file supplied. Use --inspect first, then run with --file/--literacy-col/--outcome-cols.")
        return 0

    if not args.literacy_col or not args.outcome_cols:
        raise ValueError("You must provide --literacy-col and --outcome-cols.")

    df = read_table(args.file, sheet=args.sheet)
    covariates = split_cols(args.covariates)
    outcome_cols = split_cols(args.outcome_cols)

    long = build_long(
        df=df,
        literacy_col=args.literacy_col,
        outcome_cols=outcome_cols,
        id_col=args.id_col,
        covariates=covariates,
    )

    id_col = args.id_col if args.id_col in df.columns else "__row_id__"

    print_header("Data summary")
    print(f"N rows in original data: {len(df)}")
    print(f"N item-level rows used: {len(long)}")
    print(f"N participants: {long[id_col].nunique()}")
    print(f"Outcome categories: {sorted(long['y'].unique())}")
    print(f"Tasks/items: {long['task'].nunique()}")
    print(long[["y", "z_literacy"]].describe().to_string())

    fit_ols_average(long, id_col=id_col, literacy_col=args.literacy_col, covariates=covariates)
    fit_binary_logit(long, covariates=covariates, threshold=args.threshold)
    fit_ordered_logit(long, covariates=covariates)
    fit_multinomial_logit(long, covariates=covariates)
    predicted_probabilities_ordered(long, covariates=covariates)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
