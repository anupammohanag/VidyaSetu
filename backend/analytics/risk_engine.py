import pandas as pd
import numpy as np
import sqlite3
import os
import json

PROCESSED_DIR = "../data/processed"
DB_PATH = "../data/vidyasetu.db"

def calculate_retention_risk():
    print("Loading processed datasets...")
    df_school = pd.read_csv(f"{PROCESSED_DIR}/processed_school_master.csv")
    df_att = pd.read_csv(f"{PROCESSED_DIR}/processed_attendance.csv")
    df_infra = pd.read_csv(f"{PROCESSED_DIR}/processed_infrastructure.csv")
    
    # Handle optional datasets
    has_mdm = os.path.exists(f"{PROCESSED_DIR}/processed_mdm.csv")
    if has_mdm:
        df_mdm = pd.read_csv(f"{PROCESSED_DIR}/processed_mdm.csv")
    
    has_scores = os.path.exists(f"{PROCESSED_DIR}/processed_test_scores.csv")
    if has_scores:
        df_scores = pd.read_csv(f"{PROCESSED_DIR}/processed_test_scores.csv")
        
    print("Calculating per-school metrics...")
    
    # 1. Attendance Metrics
    # Exclude proxy attendance for genuine rate? Let's just use valid records.
    valid_att = df_att[df_att['impossible_attendance'] == False].copy()
    valid_att['att_rate'] = np.where(valid_att['total_students'] > 0, 
                                     valid_att['present_students'] / valid_att['total_students'], 0)
    
    school_att = valid_att.groupby('school_id_clean')['att_rate'].mean().reset_index()
    school_att.rename(columns={'att_rate': 'avg_attendance_rate'}, inplace=True)
    
    # 2. Infrastructure Deficit
    # Use latest inspection or mean deficit
    school_infra = df_infra.groupby('school_id_clean')['infrastructure_deficit_index'].mean().reset_index()
    
    # 3. MDM Consistency (if available)
    if has_mdm:
        # MDM consistency: distinct dates with MDM procurement / distinct dates with attendance
        mdm_dates = df_mdm.groupby('school_id_clean')['date_clean'].nunique().reset_index(name='mdm_days')
        att_dates = valid_att.groupby('school_id_clean')['date_clean'].nunique().reset_index(name='att_days')
        mdm_consistency = pd.merge(att_dates, mdm_dates, on='school_id_clean', how='left').fillna(0)
        mdm_consistency['mdm_regularity_score'] = np.where(mdm_consistency['att_days'] > 0,
                                                           mdm_consistency['mdm_days'] / mdm_consistency['att_days'], 0)
        # Cap at 1.0
        mdm_consistency['mdm_regularity_score'] = mdm_consistency['mdm_regularity_score'].clip(upper=1.0)
    else:
        mdm_consistency = pd.DataFrame(columns=['school_id_clean', 'mdm_regularity_score'])
        
    # 4. Learning Outcomes
    if has_scores:
        school_scores = df_scores.groupby('school_id_clean')['score_percentage_clean'].mean().reset_index()
        school_scores.rename(columns={'score_percentage_clean': 'avg_test_score'}, inplace=True)
    else:
        school_scores = pd.DataFrame(columns=['school_id_clean', 'avg_test_score'])
        
    # Merge all metrics
    risk_df = df_school[['school_id_clean', 'school_name', 'district']].copy()
    risk_df = pd.merge(risk_df, school_att, on='school_id_clean', how='left')
    risk_df = pd.merge(risk_df, school_infra, on='school_id_clean', how='left')
    
    if has_mdm:
        risk_df = pd.merge(risk_df, mdm_consistency[['school_id_clean', 'mdm_regularity_score']], on='school_id_clean', how='left')
    else:
        risk_df['mdm_regularity_score'] = 1.0 # default if no data
        
    if has_scores:
        risk_df = pd.merge(risk_df, school_scores, on='school_id_clean', how='left')
    else:
        risk_df['avg_test_score'] = 100.0
        
    # Fill NAs
    risk_df['avg_attendance_rate'] = risk_df['avg_attendance_rate'].fillna(risk_df['avg_attendance_rate'].mean())
    risk_df['infrastructure_deficit_index'] = risk_df['infrastructure_deficit_index'].fillna(risk_df['infrastructure_deficit_index'].mean())
    risk_df['mdm_regularity_score'] = risk_df['mdm_regularity_score'].fillna(0)
    risk_df['avg_test_score'] = risk_df['avg_test_score'].fillna(risk_df['avg_test_score'].mean())
    
    # Calculate Risk Score (0 to 1, higher is worse)
    # Weights: Attendance: 40%, Infra: 20%, MDM: 20%, Scores: 20%
    att_risk = 1.0 - risk_df['avg_attendance_rate']
    infra_risk = risk_df['infrastructure_deficit_index']
    mdm_risk = 1.0 - risk_df['mdm_regularity_score']
    score_risk = 1.0 - (risk_df['avg_test_score'] / 100.0)
    
    risk_df['risk_score'] = (att_risk * 0.4) + (infra_risk * 0.2) + (mdm_risk * 0.2) + (score_risk * 0.2)
    
    # Classify
    def classify_risk(score):
        if score > 0.6: return "HIGH"
        if score > 0.4: return "MEDIUM"
        return "LOW"
    
    risk_df['risk_category'] = risk_df['risk_score'].apply(classify_risk)
    
    # Generate Reasons for HIGH risk
    def generate_reasons(row):
        if row['risk_category'] != "HIGH": return "[]"
        reasons = []
        if row['avg_attendance_rate'] < 0.6: reasons.append("Severe attendance deficit (<60%)")
        elif row['avg_attendance_rate'] < 0.75: reasons.append("Low attendance (<75%)")
        
        if row['infrastructure_deficit_index'] > 0.5: reasons.append("Major infrastructure deficit")
        
        if row['mdm_regularity_score'] < 0.5: reasons.append("Highly irregular MDM provision")
        
        if row['avg_test_score'] < 50: reasons.append("Poor learning outcomes (<50%)")
        
        return json.dumps(reasons)
        
    risk_df['risk_reasons'] = risk_df.apply(generate_reasons, axis=1)
    
    print("Risk metrics calculated.")
    
    # Calculate Welfare Efficacy Analysis (MDM Consistency vs Attendance)
    # Group schools into High/Low MDM consistency and get avg attendance
    mdm_median = risk_df['mdm_regularity_score'].median()
    high_mdm_att = risk_df[risk_df['mdm_regularity_score'] >= mdm_median]['avg_attendance_rate'].mean()
    low_mdm_att = risk_df[risk_df['mdm_regularity_score'] < mdm_median]['avg_attendance_rate'].mean()
    
    welfare_efficacy = pd.DataFrame([
        {'mdm_consistency': 'High', 'avg_attendance': high_mdm_att},
        {'mdm_consistency': 'Low', 'avg_attendance': low_mdm_att}
    ])
    
    # Calculate Bonus Query: Compare avg test scores with/without functional electricity
    elec_status = df_infra.groupby('school_id_clean')['has_electricity_clean'].max().reset_index() # max gives True if any True
    elec_scores = pd.merge(elec_status, school_scores, on='school_id_clean', how='inner')
    
    has_elec_score = elec_scores[elec_scores['has_electricity_clean'] == True]['avg_test_score'].mean()
    no_elec_score = elec_scores[elec_scores['has_electricity_clean'] == False]['avg_test_score'].mean()
    
    bonus_query_results = pd.DataFrame([
        {'has_electricity': True, 'avg_test_score': has_elec_score},
        {'has_electricity': False, 'avg_test_score': no_elec_score},
        {'has_electricity': 'Difference', 'avg_test_score': has_elec_score - no_elec_score}
    ])
    
    print("Loading into SQLite database...")
    # Store everything in SQLite
    conn = sqlite3.connect(DB_PATH)
    df_school.to_sql('school_master', conn, if_exists='replace', index=False)
    df_att.to_sql('attendance', conn, if_exists='replace', index=False)
    df_infra.to_sql('infrastructure', conn, if_exists='replace', index=False)
    if has_mdm: df_mdm.to_sql('mdm', conn, if_exists='replace', index=False)
    if has_scores: df_scores.to_sql('test_scores', conn, if_exists='replace', index=False)
    
    risk_df.to_sql('retention_risk', conn, if_exists='replace', index=False)
    welfare_efficacy.to_sql('welfare_efficacy', conn, if_exists='replace', index=False)
    bonus_query_results.to_sql('bonus_query_electricity_vs_scores', conn, if_exists='replace', index=False)
    
    conn.close()
    print(f"Database successfully saved to {DB_PATH}")

if __name__ == "__main__":
    calculate_retention_risk()
