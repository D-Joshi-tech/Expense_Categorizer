import streamlit as st
import pandas as pd

from src.config import DEFAULT_CATEGORIES, DEFAULT_MERCHANT_RULES
from src.ingest import ingest_csv
from src.llm_client import OllamaClient, DisabledLLMClient
from src.categorize import categorize_one
from src.anomalies import detect_anomalies
from src.trends import monthly_trend, monthly_totals
from src.report_pdf import generate_pdf_report

st.set_page_config(page_title="AI Expense Categorizer", layout="wide")
st.title("AI Expense Categorizer (Hybrid Rules + AI)")

# -------- Session state init --------
if "categories" not in st.session_state:
    st.session_state["categories"] = DEFAULT_CATEGORIES.copy()

if "merchant_rules" not in st.session_state:
    # store rules as dict
    st.session_state["merchant_rules"] = DEFAULT_MERCHANT_RULES.copy()

# -------- Sidebar controls --------
with st.sidebar:
    st.subheader("LLM Settings (Free-tier friendly)")
    llm_enabled = st.checkbox("Enable LLM (Ollama local)", value=True)
    ollama_model = st.text_input("Ollama model", value="llama3.1:8b")
    ollama_url = st.text_input("Ollama base URL", value="http://localhost:11434")

    st.divider()
    st.subheader("Anomaly Thresholds")
    manual_threshold_on = st.checkbox("Enable manual high-amount threshold", value=False)
    manual_high_amt = st.number_input("High amount threshold", min_value=0.0, value=25000.0, step=1000.0)

    st.divider()
    st.subheader("Processing Options")
    max_rows = st.number_input("Max rows to process (demo safety)", min_value=50, max_value=20000, value=2000, step=50)

# -------- Categories editor --------
st.write("## Editable Categories")
st.caption("Edit categories for this session. Keep them concise and consistent.")

cat_text = st.text_area(
    "One category per line",
    value="\n".join(st.session_state["categories"]),
    height=160
)

colA, colB = st.columns([1, 1])
with colA:
    if st.button("Update categories"):
        updated = [c.strip() for c in cat_text.splitlines() if c.strip()]
        # Always ensure Other exists
        if "Other" not in updated:
            updated.append("Other")
        st.session_state["categories"] = updated
        st.success(f"Updated categories: {len(updated)}")
with colB:
    if st.button("Reset to default categories"):
        st.session_state["categories"] = DEFAULT_CATEGORIES.copy()
        st.success("Reset categories to defaults.")

# -------- Merchant rules editor --------
st.write("## Rule-based Mapping (Optional but recommended)")
st.caption("Format: KEYWORD = Category. Rules run first, then LLM handles the rest.")

rules_df = pd.DataFrame(
    [{"keyword": k, "category": v} for k, v in st.session_state["merchant_rules"].items()]
)

edited_rules = st.data_editor(
    rules_df,
    use_container_width=True,
    num_rows="dynamic",
    key="rules_editor"
)

colR1, colR2 = st.columns([1, 1])
with colR1:
    if st.button("Save rules"):
        new_rules = {}
        for _, row in edited_rules.iterrows():
            k = str(row.get("keyword", "")).strip()
            v = str(row.get("category", "")).strip()
            if k and v:
                new_rules[k.upper()] = v
        st.session_state["merchant_rules"] = new_rules
        st.success(f"Saved {len(new_rules)} rules.")
with colR2:
    if st.button("Reset rules to default"):
        st.session_state["merchant_rules"] = DEFAULT_MERCHANT_RULES.copy()
        st.success("Reset rules to defaults.")

# -------- Upload CSV --------
st.write("## Upload Expense CSV")
uploaded = st.file_uploader("Upload CSV with columns: date, amount, description", type=["csv"])

if not uploaded:
    st.info("Upload a CSV to begin.")
    st.stop()

# -------- Ingestion --------
try:
    df = ingest_csv(uploaded)
except Exception as e:
    st.error(f"CSV ingestion failed: {e}")
    st.stop()

st.success(f"Loaded {len(df)} rows.")

invalid = df[~df["row_valid"]]
df_ok = df[df["row_valid"]].copy()

if len(invalid) > 0:
    st.warning(f"{len(invalid)} invalid/malformed rows detected (will be excluded).")
    with st.expander("Show invalid rows"):
        st.dataframe(invalid.head(50), use_container_width=True)

# Limit for demo safety
if len(df_ok) > max_rows:
    st.warning(f"Dataset has {len(df_ok)} valid rows; processing only first {max_rows} (change in sidebar).")
    df_ok = df_ok.head(int(max_rows)).copy()

st.write("### Preview (valid rows)")
st.dataframe(df_ok.head(20), use_container_width=True)

# -------- Run pipeline --------
run = st.button("Run Categorization + Anomaly Detection", type="primary")

if run:
    categories = st.session_state["categories"]
    merchant_rules = st.session_state["merchant_rules"]

    if llm_enabled:
        llm_client = OllamaClient(base_url=ollama_url, model=ollama_model)
    else:
        llm_client = DisabledLLMClient()

    results = []
    for desc in df_ok["description"].tolist():
        results.append(categorize_one(desc, llm_client, categories, merchant_rules))

    res_df = pd.DataFrame(results)
    df_out = pd.concat([df_ok.reset_index(drop=True), res_df], axis=1)

    df_out = detect_anomalies(
        df_out,
        manual_high_threshold=(manual_high_amt if (manual_threshold_on and manual_high_amt > 0) else None)
    )

    st.session_state["df_out"] = df_out

# -------- Show outputs --------
if "df_out" not in st.session_state:
    st.stop()

df_out = st.session_state["df_out"]

st.write("## Categorized Transactions")
st.dataframe(df_out, use_container_width=True)

# Summary by category
st.write("## Summary Report")

summary = (
    df_out.groupby("category")["amount"].sum()
    .reset_index()
    .sort_values("amount", ascending=False)
)

total_spend = summary["amount"].sum() if len(summary) else 0.0
summary["percent"] = (summary["amount"] / total_spend * 100).round(2) if total_spend else 0.0

col1, col2, col3 = st.columns(3)
col1.metric("Total spend", f"{total_spend:.2f}")
col2.metric("Transactions processed", f"{len(df_out)}")
col3.metric("Anomalies flagged", f"{int(df_out['is_anomaly'].sum())}")

st.dataframe(summary, use_container_width=True)

# Monthly trend analysis
st.write("## Monthly Trend Analysis")

m_tot = monthly_totals(df_out)
m_pivot = monthly_trend(df_out)

colT1, colT2 = st.columns([1, 1])
with colT1:
    st.write("### Monthly totals")
    st.line_chart(m_tot.set_index("month")["amount"])
    st.dataframe(m_tot, use_container_width=True)
with colT2:
    st.write("### Monthly by category")
    # line chart: multiple series
    if len(m_pivot) > 0 and len(m_pivot.columns) > 1:
        st.line_chart(m_pivot.set_index("month"))
    st.dataframe(m_pivot, use_container_width=True)

# Anomalies
st.write("## Anomalies")
anom = df_out[df_out["is_anomaly"]].copy()
if len(anom) > 0:
    st.dataframe(anom[["date", "amount", "description", "category", "confidence", "method", "anomaly_labels"]], use_container_width=True)
else:
    st.info("No anomalies flagged.")

# Downloads: CSV + PDF
st.write("## Export Reports")

csv_bytes = df_out.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download categorized CSV",
    data=csv_bytes,
    file_name="categorized_expenses.csv",
    mime="text/csv"
)

pdf_bytes = generate_pdf_report(
    df_out=df_out,
    category_summary=summary,
    monthly_totals=m_tot,
    title="AI Expense Categorizer Report"
)
st.download_button(
    "Download PDF report",
    data=pdf_bytes,
    file_name="expense_report.pdf",
    mime="application/pdf"
)
