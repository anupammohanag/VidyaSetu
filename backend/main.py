from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import pandas as pd
import json
import os
from dotenv import load_dotenv
import google.generativeai as genai
from ai_agent.agent import run_agent

_ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(dotenv_path=_ENV_PATH)

app = FastAPI(title="VidyaSetu AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "../data/vidyasetu.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/api/dashboard/summary")
def get_dashboard_summary():
    conn = get_db_connection()
    try:
        total_schools = conn.execute("SELECT COUNT(*) FROM school_master").fetchone()[0]
        total_students = conn.execute("SELECT SUM(total_enrolled_students) FROM school_master").fetchone()[0]
        avg_att = conn.execute("SELECT AVG(avg_attendance_rate) FROM retention_risk").fetchone()[0] * 100
        
        total_att_records = conn.execute("SELECT COUNT(*) FROM attendance").fetchone()[0]
        proxy_records = conn.execute("SELECT COUNT(*) FROM attendance WHERE is_proxy_attendance = 1").fetchone()[0]
        proxy_rate = (proxy_records / total_att_records * 100) if total_att_records > 0 else 0
        
        infra_deficit = conn.execute("SELECT AVG(infrastructure_deficit_index) FROM retention_risk").fetchone()[0] * 100
        avg_fln = conn.execute("SELECT AVG(avg_test_score) FROM retention_risk").fetchone()[0]
        high_risk = conn.execute("SELECT COUNT(*) FROM retention_risk WHERE risk_category = 'HIGH'").fetchone()[0]
        
        return {
            "total_schools": total_schools,
            "students_tracked": total_students,
            "avg_attendance": round(avg_att, 1),
            "proxy_rate": round(proxy_rate, 2),
            "infra_deficit": round(infra_deficit, 1),
            "avg_fln": round(avg_fln, 1),
            "high_risk_schools": high_risk
        }
    finally:
        conn.close()

@app.get("/api/attendance/trend")
def get_attendance_trend():
    conn = get_db_connection()
    try:
        df = pd.read_sql_query("SELECT date_clean, present_students, total_students FROM attendance WHERE impossible_attendance = 0", conn)
        df['date_clean'] = pd.to_datetime(df['date_clean'])
        df['month'] = df['date_clean'].dt.to_period('M').astype(str)
        monthly = df.groupby('month')[['present_students', 'total_students']].sum().reset_index()
        monthly['att_rate'] = (monthly['present_students'] / monthly['total_students'] * 100).round(1)
        return monthly[['month', 'att_rate']].to_dict(orient='records')
    finally:
        conn.close()

@app.get("/api/risk/schools")
def get_risk_schools():
    conn = get_db_connection()
    try:
        query = "SELECT school_id_clean, school_name, district, risk_score, risk_category, risk_reasons FROM retention_risk ORDER BY risk_score DESC LIMIT 50"
        df = pd.read_sql_query(query, conn)
        df['risk_reasons'] = df['risk_reasons'].apply(lambda x: json.loads(x) if pd.notna(x) and isinstance(x, str) else [])
        df = df.astype(object).where(pd.notna(df), None)
        return df.to_dict(orient='records')
    finally:
        conn.close()

@app.get("/api/data-quality")
def get_data_quality():
    conn = get_db_connection()
    try:
        total_att = conn.execute("SELECT COUNT(*) FROM attendance").fetchone()[0]
        proxy = conn.execute("SELECT COUNT(*) FROM attendance WHERE is_proxy_attendance = 1").fetchone()[0]
        impossible = conn.execute("SELECT COUNT(*) FROM attendance WHERE impossible_attendance = 1").fetchone()[0]
        
        return {
            "total_attendance_records": total_att,
            "proxy_attendance_records": proxy,
            "impossible_attendance_records": impossible,
            "standardized_ids": True
        }
    finally:
        conn.close()

@app.get("/api/schools")
def get_schools_list():
    conn = get_db_connection()
    try:
        schools = conn.execute("SELECT school_id_clean, school_name, district, risk_category FROM retention_risk").fetchall()
        return [dict(s) for s in schools]
    finally:
        conn.close()

@app.get("/api/schools/{school_id}")
def get_school_profile(school_id: str):
    conn = get_db_connection()
    try:
        school = conn.execute("SELECT * FROM retention_risk WHERE school_id_clean = ?", (school_id,)).fetchone()
        if not school:
            raise HTTPException(status_code=404, detail="School not found")
        
        res = dict(school)
        res['risk_reasons'] = json.loads(res['risk_reasons']) if pd.notna(res['risk_reasons']) else []
        return res
    finally:
        conn.close()

@app.get("/api/districts")
def get_districts():
    conn = get_db_connection()
    try:
        query = """
        SELECT district, 
               AVG(avg_attendance_rate)*100 as avg_attendance, 
               AVG(avg_test_score) as avg_score,
               COUNT(school_id_clean) as total_schools
        FROM retention_risk 
        GROUP BY district
        """
        districts = conn.execute(query).fetchall()
        return [dict(d) for d in districts]
    finally:
        conn.close()

class AIQuery(BaseModel):
    query: str

@app.post("/api/ai/query")
def post_ai_query(query_req: AIQuery):
    """
    VidyaSetu AI Agent endpoint.
    Uses Gemini function-calling to intelligently route queries to the correct
    backend analytics tools and return verified, data-backed answers.
    Response format is preserved: answer, chart_type, chart_data.
    """
    return run_agent(query_req.query)
