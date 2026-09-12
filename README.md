# VidyaSetu AI

VidyaSetu AI is an end-to-end automated decision-support platform built for the **Education & EdTech Hackathon**. It is designed to track and analyze the relationship between the Mid-Day Meal scheme, school infrastructure, student attendance, learning outcomes, and student retention risk.

## Problem Statement
The State Education Department needs to convert messy education and welfare datasets into actionable insights for education officers, answering questions about attendance drops, infrastructure gaps, and high-risk schools requiring intervention.

## Solution Architecture
1. **Data Cleaning Pipeline** (`backend/data_processing/clean_pipeline.py`): A Python Pandas engine that standardizes IDs, cleans anomalies, normalizes inputs, and handles missing values transparently without blindly deleting records.
2. **Analytics Engine** (`backend/analytics/risk_engine.py`): Calculates a 360-degree **Retention Risk Indicator** for schools using multi-factor weighted scoring.
3. **Backend API** (`backend/main.py`): A FastAPI service backed by SQLite serving computed metrics.
4. **AI Agent**: Integrated Gemini AI capable of answering natural language questions deterministically via the API.
5. **Dashboard**: A React + Vite + TailwindCSS application providing executive KPI views and deep dives into priority schools.

## Project Structure
```text
vidyasetu-ai/
├── frontend/ (React UI)
├── backend/ (FastAPI & Pipeline)
│   ├── data_processing/
│   ├── analytics/
│   └── main.py
├── data/
│   ├── raw/ (Raw hackathon data)
│   ├── processed/ (Cleaned CSVs)
│   └── vidyasetu.db (Analytical SQLite DB)
```

## Running the Application

### Backend Setup
```bash
cd backend
python -m venv venv
# Activate venv: .\venv\Scripts\activate
pip install -r requirements.txt

# Step 1: Run cleaning pipeline
python data_processing/clean_pipeline.py

# Step 2: Run analytics engine to build DB
python analytics/risk_engine.py

# Step 3: Run FastAPI Server (ensure GEMINI_API_KEY is in .env)
uvicorn main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## Features Demo
- **Executive Dashboard**: Displays key metrics including Proxy Attendance rate and Infra Deficit.
- **Priority Intervention List**: Schools with HIGH risk categorized based on attendance, infrastructure, and MDM gaps.
- **VidyaSetu AI Bot**: Ask natural language questions like "Compare average test scores between schools with and without functional electricity." (The bonus query).

## AI Strategy
The application employs a deterministic fallback mechanism for complex analytical questions where AI could hallucinate, ensuring robust calculations (e.g. comparing electricity vs test scores) are done via Pandas while the LLM interprets the results.
