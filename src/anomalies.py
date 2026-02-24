import numpy as np
import pandas as pd
from src.utils import normalize_for_match

def mad_flags(series: pd.Series, k: float = 4.0) -> pd.Series:
    x = series.dropna().values
    if len(x) < 10:
        return pd.Series([False] * len(series), index=series.index)

    med = np.median(x)
    mad = np.median(np.abs(x - med))
    if mad == 0:
        mad = np.std(x) if np.std(x) > 0 else 1.0

    threshold = med + k * mad
    return series > threshold

def detect_anomalies(df: pd.DataFrame, manual_high_threshold: float | None = None) -> pd.DataFrame:
    out = df.copy()
    out["anomaly_labels"] = ""

    # Statistical high amounts across all expenses
    high_all = mad_flags(out["amount"], k=4.0)
    out.loc[high_all, "anomaly_labels"] += "High amount (statistical); "

    # Manual high amount threshold (user-defined)
    if manual_high_threshold is not None and manual_high_threshold > 0:
        out.loc[out["amount"] > manual_high_threshold, "anomaly_labels"] += f"High amount (> {manual_high_threshold}); "

    # Possible duplicates
    out["desc_norm"] = out["description"].fillna("").map(normalize_for_match)
    key = out["date"].astype(str) + "|" + out["amount"].astype(str) + "|" + out["desc_norm"]
    dup = key.duplicated(keep=False)
    out.loc[dup, "anomaly_labels"] += "Possible duplicate; "

    # Out-of-pattern within category (after categorization)
    if "category" in out.columns:
        out["cat_outlier"] = False
        for cat, g in out.groupby("category"):
            flags = mad_flags(g["amount"], k=4.0)
            out.loc[g.index, "cat_outlier"] = flags.values
        out.loc[out["cat_outlier"], "anomaly_labels"] += "Unusual for category; "
        out.drop(columns=["cat_outlier"], inplace=True, errors="ignore")

    out["is_anomaly"] = out["anomaly_labels"].str.len().gt(0)

    out.drop(columns=["desc_norm"], inplace=True, errors="ignore")
    return out