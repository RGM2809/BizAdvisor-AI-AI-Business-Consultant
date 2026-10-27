<<<<<<< HEAD
# BizAdvisor AI

BizAdvisor AI is a local-first business analytics and consulting dashboard for small businesses. It uses sales and expense data to show business performance, forecast sales, and surface practical recommendations.

## Features

- Create and manage business profiles.
- Import sales data from CSV and Excel files, or enter data manually.
- Validate, standardize, and store sales transactions in a local SQLite database.
- Track business expenses and review financial summaries.
- Explore sales trends, product performance, and business insights.
- Forecast sales and ask questions about business data.

## Requirements

- Python 3.10 or newer
- pip

## Installation

Clone the repository and move into the project directory:

```bash
git clone https://github.com/RGM2809/BizAdvisor-AI-AI-Business-Consultant.git
cd BizAdvisor-AI-AI-Business-Consultant
```

Create and activate a virtual environment, then install dependencies:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

macOS or Linux:

```bash
source .venv/bin/activate
```

Install the packages:

```bash
python -m pip install -r requirements.txt
```

## Run the application

```bash
python -m streamlit run app.py
```

Streamlit will print a local URL to open in your browser. Use the pages in the sidebar to set up a business, import data, and explore reports.

## Run tests

```bash
python -m pytest -q
```

## Data and privacy

Application data is stored locally in SQLite under `data/`. Database files, virtual environments, caches, and local secrets are excluded from Git by `.gitignore`. Back up the database separately if you need to preserve locally entered business data.

## Technology

Python, Streamlit, pandas, NumPy, SQLite, Plotly, scikit-learn, statsmodels, and pytest.

# BizAdvisor-AI-AI-Business-Consultant

