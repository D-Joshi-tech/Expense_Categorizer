import pandas as pd

def monthly_trend(df: pd.DataFrame) -> pd.DataFrame:
    temp = df.copy()
    temp["month"] = temp["date"].dt.to_period("M").astype(str)
    pivot = temp.pivot_table(
        index="month",
        columns="category",
        values="amount",
        aggfunc="sum",
        fill_value=0.0
    ).reset_index()
    return pivot.sort_values("month")

def monthly_totals(df: pd.DataFrame) -> pd.DataFrame:
    temp = df.copy()
    temp["month"] = temp["date"].dt.to_period("M").astype(str)
    out = temp.groupby("month")["amount"].sum().reset_index().sort_values("month")
    return out