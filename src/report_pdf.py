from io import BytesIO
from typing import Optional
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def generate_pdf_report(
    df_out: pd.DataFrame,
    category_summary: pd.DataFrame,
    monthly_totals: pd.DataFrame,
    title: str = "AI Expense Categorizer Report",
) -> bytes:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 50
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, title)

    y -= 25
    c.setFont("Helvetica", 10)
    c.drawString(50, y, f"Total rows processed: {len(df_out)}")
    y -= 15
    anomalies_count = int(df_out["is_anomaly"].sum()) if "is_anomaly" in df_out.columns else 0
    c.drawString(50, y, f"Anomalies flagged: {anomalies_count}")

    # Category Summary
    y -= 30
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Spending by Category")

    y -= 18
    c.setFont("Helvetica", 9)
    c.drawString(50, y, "Category")
    c.drawString(260, y, "Total")
    c.drawString(360, y, "Percent")

    y -= 12
    for _, row in category_summary.head(12).iterrows():
        if y < 80:
            c.showPage()
            y = height - 50
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y, "Spending by Category (cont.)")
            y -= 20
            c.setFont("Helvetica", 9)
        c.drawString(50, y, str(row["category"])[:30])
        c.drawString(260, y, f"{row['amount']:.2f}")
        c.drawString(360, y, f"{row['percent']:.2f}%")
        y -= 12

    # Monthly totals
    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Monthly Totals")

    y -= 18
    c.setFont("Helvetica", 9)
    c.drawString(50, y, "Month")
    c.drawString(260, y, "Total")

    y -= 12
    for _, row in monthly_totals.iterrows():
        if y < 80:
            c.showPage()
            y = height - 50
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y, "Monthly Totals (cont.)")
            y -= 20
            c.setFont("Helvetica", 9)
        c.drawString(50, y, str(row["month"]))
        c.drawString(260, y, f"{row['amount']:.2f}")
        y -= 12

    # Anomalies section (top 15)
    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Anomalies (Top 15)")

    y -= 18
    c.setFont("Helvetica", 8)
    anom = df_out[df_out.get("is_anomaly", False)].copy()
    anom = anom.head(15)

    for _, row in anom.iterrows():
        if y < 80:
            c.showPage()
            y = height - 50
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y, "Anomalies (cont.)")
            y -= 20
            c.setFont("Helvetica", 8)

        line = f"{row['date'].date()} | {row['amount']:.2f} | {str(row['category'])} | {str(row['description'])[:50]} | {str(row['anomaly_labels'])[:45]}"
        c.drawString(50, y, line)
        y -= 11

    c.showPage()
    c.save()
    return buffer.getvalue()