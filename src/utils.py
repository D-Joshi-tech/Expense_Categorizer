import re
from typing import Any

def normalize_text(x: Any) -> str:
    if x is None:
        return ""
    s = str(x).strip()
    s = re.sub(r"\s+", " ", s)
    return s

def normalize_for_match(s: str) -> str:
    s = normalize_text(s).upper()
    s = re.sub(r"[^A-Z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def safe_float(x: Any) -> float | None:
    try:
        return float(x)
    except Exception:
        return None