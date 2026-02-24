# AI Expense Categorizer

An AI-assisted expense processing tool that automatically categorizes transactions, detects anomalies, and generates summary reports from CSV expense data.

This project demonstrates a hybrid rule-based + LLM approach to improve accuracy, consistency, and efficiency in financial data processing.


##  Features

- CSV expense ingestion with validation
- Hybrid categorization (Rule-based + LLM)
- Confidence scores per classification
- Anomaly detection (duplicates, high amounts, outliers)
- Monthly trend analysis
- Editable category list
- Exportable reports (CSV & PDF)
- Interactive Streamlit UI


##  Tech Stack

- **Backend / Logic:** Python
- **Data Processing:** Pandas, NumPy
- **LLM:** Ollama (local, free-tier)
- **Frontend:** Streamlit
- **PDF Generation:** ReportLab

## 📂 Project Structure

-ai-expense-categorizer/
  -app.py
  -requirements.txt
  -sample_data/
    -expenses_sample.csv
    -expenses_with_anomalies.csv
  -src/
    -config.py
    -ingest.py
    -utils.py
    -llm_client.py
    -categorize.py
    -anomalies.py
    -trends.py
    -report_pdf.py


---

##  Setup Instructions

### Clone repository
*bash command*
git clone https://github.com/D-Joshi-tech/Expense_Categorizer
cd ai-expense-categorizer


### Create virtual environment
py -m venv .venv
.venv\Scripts\activate


### Install dependencies
python -m pip install -r requirements.txt


### (Optional) Install Ollama for LLM categorization

Download from: https://ollama.com

ollama pull llama3.1:8b


### Run Streamlit app
python -m streamlit run app.py
