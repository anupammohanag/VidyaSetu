import sqlite3
import pandas as pd
import os
import json

DB_PATH = os.path.join(os.path.dirname(__file__), "../../data/vidyasetu.db")

def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_dashboard_summary():
    """Returns an overall high-level summary of the VidyaSetu dashboard including total schools, students, average attendance, proxy rate, infrastructure deficit, FLN score, and number of high-risk schools."""
    conn = _get_conn()
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
            "data": {
                "total_schools": total_schools,
                "students_tracked": total_students,
                "avg_attendance_percent": round(avg_att, 1),
                "proxy_attendance_rate_percent": round(proxy_rate, 2),
                "avg_infrastructure_deficit_percent": round(infra_deficit, 1),
                "avg_fln_test_score_percent": round(avg_fln, 1),
                "high_risk_schools": high_risk
            }
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

def get_attendance_analysis(district: str = None):
    """
    Returns an analysis of attendance across the project. Optionally filter by district.
    Provides average attendance, and the list of top 5 and bottom 5 schools by attendance.
    """
    conn = _get_conn()
    try:
        query = "SELECT school_id_clean, school_name, district, avg_attendance_rate FROM retention_risk"
        params = ()
        if district:
            query += " WHERE district = ?"
            params = (district,)
        
        df = pd.read_sql_query(query, conn, params=params)
        if df.empty:
            return {"error": "No data found"}
            
        df['avg_attendance_percent'] = (df['avg_attendance_rate'] * 100).round(1)
        avg_att = df['avg_attendance_percent'].mean().round(1)
        
        top_5 = df.nlargest(5, 'avg_attendance_percent')[['school_name', 'district', 'avg_attendance_percent']].to_dict('records')
        bottom_5 = df.nsmallest(5, 'avg_attendance_percent')[['school_name', 'district', 'avg_attendance_percent']].to_dict('records')
        
        # Format chart data
        chart_data = [{"name": s['school_name'][:15] + "..", "Attendance": s['avg_attendance_percent']} for s in bottom_5]
        
        return {
            "data": {
                "overall_avg_attendance_percent": avg_att,
                "district_filtered": district or "All",
                "top_5_schools": top_5,
                "bottom_5_schools": bottom_5
            },
            "chart_type": "bar" if len(bottom_5) > 0 else None,
            "chart_data": chart_data if len(bottom_5) > 0 else None
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

def get_mdm_analysis(district: str = None):
    """
    Returns an analysis of Mid-Day Meal (MDM) data. Shows MDM regularity and anomalies.
    """
    conn = _get_conn()
    try:
        query = "SELECT school_name, district, mdm_regularity_score FROM retention_risk"
        params = ()
        if district:
            query += " WHERE district = ?"
            params = (district,)
            
        df = pd.read_sql_query(query, conn, params=params)
        if df.empty:
            return {"error": "No data found"}
            
        df['mdm_regularity_percent'] = (df['mdm_regularity_score'] * 100).round(1)
        avg_mdm = df['mdm_regularity_percent'].mean().round(1)
        
        bottom_5 = df.nsmallest(5, 'mdm_regularity_percent')[['school_name', 'district', 'mdm_regularity_percent']].to_dict('records')
        
        chart_data = [{"name": s['school_name'][:15] + "..", "Regularity": s['mdm_regularity_percent']} for s in bottom_5]
        
        return {
            "data": {
                "average_mdm_regularity_percent": avg_mdm,
                "district_filtered": district or "All",
                "schools_with_lowest_regularity": bottom_5
            },
            "chart_type": "bar" if len(bottom_5) > 0 else None,
            "chart_data": chart_data if len(bottom_5) > 0 else None
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

def get_infrastructure_analysis(district: str = None):
    """
    Returns an analysis of infrastructure metrics (electricity, toilets, drinking water, etc.).
    """
    conn = _get_conn()
    try:
        query = "SELECT has_electricity_clean, has_drinking_water_clean, has_functional_toilet_clean FROM infrastructure"
        if district:
            query = "SELECT i.has_electricity_clean, i.has_drinking_water_clean, i.has_functional_toilet_clean FROM infrastructure i JOIN school_master s ON i.school_id_clean = s.school_id_clean WHERE s.district = ?"
            df = pd.read_sql_query(query, conn, params=(district,))
        else:
            df = pd.read_sql_query(query, conn)
            
        if df.empty:
            return {"error": "No data found"}
            
        total = len(df)
        elec_percent = (df['has_electricity_clean'].sum() / total * 100).round(1)
        water_percent = (df['has_drinking_water_clean'].sum() / total * 100).round(1)
        toilet_percent = (df['has_functional_toilet_clean'].sum() / total * 100).round(1)
        
        chart_data = [
            {"name": "Electricity", "Percent": elec_percent},
            {"name": "Drinking Water", "Percent": water_percent},
            {"name": "Functional Toilet", "Percent": toilet_percent}
        ]
        
        return {
            "data": {
                "total_inspections": total,
                "district_filtered": district or "All",
                "percent_with_electricity": elec_percent,
                "percent_with_drinking_water": water_percent,
                "percent_with_functional_toilet": toilet_percent
            },
            "chart_type": "bar",
            "chart_data": chart_data
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

def get_learning_analysis(district: str = None):
    """
    Returns an analysis of average test scores (FLN scores) across schools.
    """
    conn = _get_conn()
    try:
        query = "SELECT school_name, district, avg_test_score FROM retention_risk"
        params = ()
        if district:
            query += " WHERE district = ?"
            params = (district,)
            
        df = pd.read_sql_query(query, conn, params=params)
        if df.empty:
            return {"error": "No data found"}
            
        avg_score = df['avg_test_score'].mean().round(1)
        
        top_5 = df.nlargest(5, 'avg_test_score')[['school_name', 'district', 'avg_test_score']].to_dict('records')
        bottom_5 = df.nsmallest(5, 'avg_test_score')[['school_name', 'district', 'avg_test_score']].to_dict('records')
        
        return {
            "data": {
                "average_test_score": avg_score,
                "district_filtered": district or "All",
                "top_5_schools_scores": top_5,
                "bottom_5_schools_scores": bottom_5
            }
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

def get_risk_analysis(district: str = None):
    """
    Returns an analysis of the retention risk index or early warning risk score.
    Finds the highest risk schools and the reasons they are at risk.
    """
    conn = _get_conn()
    try:
        query = "SELECT school_name, district, risk_score, risk_category, risk_reasons FROM retention_risk"
        params = ()
        if district:
            query += " WHERE district = ?"
            params = (district,)
            
        df = pd.read_sql_query(query, conn, params=params)
        if df.empty:
            return {"error": "No data found"}
            
        counts = df['risk_category'].value_counts().to_dict()
        
        highest_risk = df.nlargest(5, 'risk_score')[['school_name', 'district', 'risk_score', 'risk_reasons']].to_dict('records')
        for r in highest_risk:
            if isinstance(r['risk_reasons'], str):
                r['risk_reasons'] = json.loads(r['risk_reasons'])
                
        chart_data = [{"name": k, "Count": v} for k, v in counts.items()]
        
        return {
            "data": {
                "risk_category_counts": counts,
                "district_filtered": district or "All",
                "top_highest_risk_schools": highest_risk
            },
            "chart_type": "bar",
            "chart_data": chart_data
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

def get_school_details(school_name: str):
    """
    Returns specific data for a single school given its exact or partial name.
    Useful for "Why is School ABC at risk?" or "Tell me about XYZ school"
    """
    conn = _get_conn()
    try:
        # Using LIKE to find partial matches
        query = "SELECT * FROM retention_risk WHERE school_name LIKE ? LIMIT 1"
        res = conn.execute(query, (f"%{school_name}%",)).fetchone()
        
        if not res:
            return {"error": f"School matching '{school_name}' not found."}
            
        data = dict(res)
        if isinstance(data.get('risk_reasons'), str):
            data['risk_reasons'] = json.loads(data['risk_reasons'])
            
        return {"data": data}
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

def get_district_analysis(district: str):
    """
    Returns summary statistics for a specific district.
    """
    conn = _get_conn()
    try:
        query = "SELECT COUNT(school_id_clean) as total_schools, AVG(avg_attendance_rate)*100 as avg_att, AVG(avg_test_score) as avg_score, AVG(infrastructure_deficit_index)*100 as avg_infra_deficit FROM retention_risk WHERE district = ?"
        res = conn.execute(query, (district,)).fetchone()
        
        if not res or res['total_schools'] == 0:
            return {"error": f"District '{district}' not found or has no data."}
            
        return {
            "data": {
                "district": district,
                "total_schools": res['total_schools'],
                "avg_attendance_percent": round(res['avg_att'] or 0, 1),
                "avg_test_score": round(res['avg_score'] or 0, 1),
                "avg_infrastructure_deficit": round(res['avg_infra_deficit'] or 0, 1)
            }
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

def get_all_districts_ranked():
    """
    Returns all districts ranked by average attendance, test scores, and infrastructure deficit.
    Use this to find which district has the highest or lowest attendance, scores, or infrastructure issues.
    """
    conn = _get_conn()
    try:
        query = """
        SELECT LOWER(district) as district_key,
               COUNT(school_id_clean) as total_schools,
               AVG(avg_attendance_rate)*100 as avg_attendance_percent,
               AVG(avg_test_score) as avg_test_score,
               AVG(infrastructure_deficit_index)*100 as avg_infra_deficit_percent
        FROM retention_risk
        WHERE district IS NOT NULL AND district != ''
        GROUP BY LOWER(district)
        ORDER BY avg_attendance_percent ASC
        """
        df = pd.read_sql_query(query, conn)
        if df.empty:
            return {"error": "No district data found"}
        
        # Normalize to title case
        df['district'] = df['district_key'].str.title()
        df = df.drop(columns=['district_key'])
        df['avg_attendance_percent'] = df['avg_attendance_percent'].round(1)
        df['avg_test_score'] = df['avg_test_score'].round(1)
        df['avg_infra_deficit_percent'] = df['avg_infra_deficit_percent'].round(1)
        
        records = df.to_dict('records')
        chart_data = [{"name": r['district'], "Attendance": r['avg_attendance_percent']} for r in records]
        
        return {
            "data": {
                "districts_ranked_by_attendance_asc": records,
                "lowest_attendance_district": records[0] if records else None,
                "highest_attendance_district": records[-1] if records else None
            },
            "chart_type": "bar",
            "chart_data": chart_data
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

def compare_electricity_scores():
    """
    Compares the average test scores between schools that have functional electricity vs those that do not.
    """
    conn = _get_conn()
    try:
        df_bonus = pd.read_sql_query("SELECT * FROM bonus_query_electricity_vs_scores", conn)
        
        has_elec = df_bonus[df_bonus['has_electricity'] == '1']['avg_test_score'].values
        no_elec = df_bonus[df_bonus['has_electricity'] == '0']['avg_test_score'].values
        diff = df_bonus[df_bonus['has_electricity'] == 'Difference']['avg_test_score'].values
        
        has_score = round(has_elec[0], 1) if len(has_elec)>0 else 0
        no_score = round(no_elec[0], 1) if len(no_elec)>0 else 0
        diff_score = round(diff[0], 1) if len(diff)>0 else 0
        
        chart_data = [
            {"name": "Functional Electricity", "Score": has_score},
            {"name": "No Functional Electricity", "Score": no_score}
        ]
        
        return {
            "data": {
                "schools_with_electricity_avg_score": has_score,
                "schools_without_electricity_avg_score": no_score,
                "score_difference": diff_score,
                "interpretation": f"In this dataset, schools with functional electricity had a {'higher' if diff_score > 0 else 'lower'} average test score."
            },
            "chart_type": "bar",
            "chart_data": chart_data
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

def compare_districts(district_a: str, district_b: str):
    """
    Compares two districts on metrics like average attendance, test scores, and infrastructure deficit.
    """
    conn = _get_conn()
    try:
        query = "SELECT district, COUNT(school_id_clean) as total_schools, AVG(avg_attendance_rate)*100 as avg_att, AVG(avg_test_score) as avg_score, AVG(infrastructure_deficit_index)*100 as avg_infra_deficit FROM retention_risk WHERE district IN (?, ?) GROUP BY district"
        df = pd.read_sql_query(query, conn, params=(district_a, district_b))
        
        if df.empty:
            return {"error": "Neither district found."}
            
        data_list = df.to_dict('records')
        
        chart_data = []
        for d in data_list:
            d['avg_att'] = round(d['avg_att'], 1) if pd.notna(d['avg_att']) else 0
            d['avg_score'] = round(d['avg_score'], 1) if pd.notna(d['avg_score']) else 0
            d['avg_infra_deficit'] = round(d['avg_infra_deficit'], 1) if pd.notna(d['avg_infra_deficit']) else 0
            chart_data.append({
                "name": d['district'],
                "Attendance": d['avg_att'],
                "Test Score": d['avg_score']
            })
            
        return {
            "data": {
                "comparison": data_list
            },
            "chart_type": "bar",
            "chart_data": chart_data
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

# List of all tools to register with Gemini
AGENT_TOOLS = [
    get_dashboard_summary,
    get_attendance_analysis,
    get_mdm_analysis,
    get_infrastructure_analysis,
    get_learning_analysis,
    get_risk_analysis,
    get_school_details,
    get_district_analysis,
    get_all_districts_ranked,
    compare_electricity_scores,
    compare_districts
]
