import pandas as pd
from src.utils import normalize_text

REQUIRED_COLS = ["date", "amount", "description"]

def ingest_csv(file) -> pd.DataFrame:
    try:
        df = pd.read_csv(file)
    except Exception as e:
        raise ValueError(f"Could not read CSV: {e}")

    df.columns = [c.strip().lower() for c in df.columns]

    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}. Required: {REQUIRED_COLS}")

    df["description"] = df["description"].apply(normalize_text)

    # Clean amount: remove commas + currency symbols
    df["amount_raw"] = df["amount"]
    df["amount"] = (
        df["amount"]
        .astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("₹", "", regex=False)
        .str.replace("$", "", regex=False)
        .str.replace("INR", "", regex=False)
        .str.replace("Rs.", "", regex=False)
        .str.strip()
    )
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")

    df["date_raw"] = df["date"]
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    df["row_valid"] = df["date"].notna() & df["amount"].notna() & df["description"].ne("")
    return df