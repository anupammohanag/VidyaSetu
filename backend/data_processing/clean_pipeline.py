import pandas as pd
import numpy as np
import re
import os
import json

RAW_DIR = "../data/raw"
PROCESSED_DIR = "../data/processed"

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def normalize_school_id(sid):
    if pd.isna(sid): return sid
    sid = str(sid).upper().replace('-', '').replace('_', '').replace(' ', '')
    nums = re.findall(r'\d+', sid)
    if nums:
        num = str(nums[0]).zfill(4)
        return f"SCH{num}"
    return sid

def parse_bool(val):
    if pd.isna(val): return None
    v = str(val).lower().strip()
    if v in ['yes', 'y', '1', 'hai', 'haan', 'functional', 'working', 'true']: return True
    if v in ['no', 'n', '0', 'nahi', 'kharab', 'broken', 'false']: return False
    return None

def normalize_vendor(v):
    if pd.isna(v): return "Unknown"
    v = str(v).lower().replace('pvt', '').replace('ltd', '').replace('private', '').replace('limited', '').replace('.', '').replace(',', '').strip()
    return ' '.join(v.split()).title()

def normalize_grain(g):
    if pd.isna(g): return "Unknown"
    g = str(g).lower().strip()
    if 'chawal' in g or 'rice' in g: return 'Rice'
    if 'gehu' in g or 'wheat' in g: return 'Wheat'
    if 'dal' in g or 'pulse' in g or 'lentil' in g: return 'Dal'
    return g.title()

def parse_mdm_quantity(qty_str):
    if pd.isna(qty_str): return 0.0
    qty_str = str(qty_str).lower().replace(',', '')
    nums = re.findall(r"[-+]?\d*\.\d+|\d+", qty_str)
    if not nums:
        return 0.0
    val = float(nums[0])
    
    if 'gram' in qty_str and 'kilogram' not in qty_str:
        return val / 1000.0
    elif 'bag' in qty_str or 'sack' in qty_str or 'bori' in qty_str:
        return val * 50.0
    else:
        return val

def parse_cost(cost_str):
    if pd.isna(cost_str): return 0.0
    cost_str = str(cost_str).replace(',', '').replace('₹', '').replace('Rs.', '').replace('Rs', '').replace('rs', '').strip()
    nums = re.findall(r"[-+]?\d*\.\d+|\d+", cost_str)
    if nums:
        return float(nums[0])
    return 0.0

def normalize_test_score(row):
    if pd.isna(row.get('avg_score')): return None
    avg_score = str(row['avg_score']).upper().strip()
    scale = str(row.get('grading_scale', '')).upper().strip()
    max_marks = str(row.get('max_marks', '100'))
    
    if '/' in avg_score:
        parts = avg_score.split('/')
        if len(parts) == 2 and parts[1].isdigit():
            try:
                return (float(parts[0]) / float(parts[1])) * 100
            except: pass

    try:
        if scale in ['PCT', 'PERCENTAGE'] or '%' in avg_score:
            return float(re.findall(r"[-+]?\d*\.\d+|\d+", avg_score)[0])
        elif scale == 'CGPA':
            val = float(re.findall(r"[-+]?\d*\.\d+|\d+", avg_score)[0])
            return min(val * 9.5, 100.0) 
        elif scale == 'LETTER GRADE' or scale == 'LETTER':
            mapping = {'A+': 95, 'A': 85, 'B': 75, 'C': 65, 'D': 55, 'E': 45, 'F': 35}
            for k in mapping:
                if avg_score.startswith(k): return float(mapping[k])
        elif max_marks and max_marks.replace('.', '', 1).isdigit() and max_marks != 'NA':
            val = float(re.findall(r"[-+]?\d*\.\d+|\d+", avg_score)[0])
            max_v = float(max_marks)
            if max_v > 0:
                return (val / max_v) * 100
    except:
        pass
    
    return None
    
def main():
    ensure_dir(PROCESSED_DIR)
    
    # 1. School Master
    print("Processing School Master...")
    df_school = pd.read_csv(f"{RAW_DIR}/track4_school_master.csv")
    df_school['school_id_clean'] = df_school['school_id'].apply(normalize_school_id)
    df_school.to_csv(f"{PROCESSED_DIR}/processed_school_master.csv", index=False)
    
    # 2. Attendance
    print("Processing Attendance...")
    df_att = pd.read_csv(f"{RAW_DIR}/track4_student_attendance.csv")
    df_att['school_id_clean'] = df_att['school_id'].apply(normalize_school_id)
    df_att['date_clean'] = pd.to_datetime(df_att['date'], errors='coerce')
    df_att['is_proxy_attendance'] = (df_att['date_clean'].dt.dayofweek == 6) & (df_att['present_students'] >= df_att['total_students'])
    df_att['impossible_attendance'] = df_att['present_students'] > df_att['total_students']
    df_att['anomaly_type'] = None
    df_att.loc[df_att['is_proxy_attendance'], 'anomaly_type'] = 'Potential proxy attendance (Sunday 100%)'
    df_att.loc[df_att['impossible_attendance'], 'anomaly_type'] = 'Impossible attendance (Present > Total)'
    df_att.to_csv(f"{PROCESSED_DIR}/processed_attendance.csv", index=False)
    
    # 3. Infrastructure
    print("Processing Infrastructure...")
    df_infra = pd.read_csv(f"{RAW_DIR}/track4_school_infrastructure.csv")
    df_infra['school_id_clean'] = df_infra['school_id'].apply(normalize_school_id)
    df_infra['date_clean'] = pd.to_datetime(df_infra['date'], errors='coerce')
    for col in ['has_electricity', 'has_drinking_water', 'has_functional_toilet', 'has_boundary_wall', 'has_playground']:
        if col in df_infra.columns:
            df_infra[f"{col}_clean"] = df_infra[col].apply(parse_bool)
            
    infra_cols = [c for c in df_infra.columns if c.endswith('_clean')]
    df_infra['infrastructure_deficit_index'] = df_infra[infra_cols].apply(lambda row: (row == False).sum() / len(infra_cols) if len(infra_cols)>0 else 0, axis=1)
    df_infra.to_csv(f"{PROCESSED_DIR}/processed_infrastructure.csv", index=False)

    # 4. MDM Procurement
    print("Processing MDM Data...")
    df_mdm = pd.read_excel(f"{RAW_DIR}/track4_mid_day_meal_procurement.xlsx")
    df_mdm['school_id_clean'] = df_mdm['school_id'].apply(normalize_school_id)
    df_mdm['date_clean'] = pd.to_datetime(df_mdm['date'], errors='coerce')
    
    # Need to verify column names for MDM, assuming reasonable names based on problem description
    col_vendor = next((c for c in df_mdm.columns if 'vendor' in c.lower()), None)
    col_grain = next((c for c in df_mdm.columns if 'grain' in c.lower() or 'item' in c.lower()), None)
    col_qty = next((c for c in df_mdm.columns if 'quant' in c.lower() or 'qty' in c.lower()), None)
    col_cost = next((c for c in df_mdm.columns if 'cost' in c.lower() or 'price' in c.lower() or 'amount' in c.lower()), None)
    
    if col_vendor: df_mdm['vendor_clean'] = df_mdm[col_vendor].apply(normalize_vendor)
    if col_grain: df_mdm['grain_clean'] = df_mdm[col_grain].apply(normalize_grain)
    if col_qty: df_mdm['qty_kg_clean'] = df_mdm[col_qty].apply(parse_mdm_quantity)
    if col_cost: df_mdm['cost_clean'] = df_mdm[col_cost].apply(parse_cost)
    
    # Calculate Cost per KG
    if col_qty and col_cost:
        df_mdm['cost_per_kg'] = np.where(df_mdm['qty_kg_clean'] > 0, df_mdm['cost_clean'] / df_mdm['qty_kg_clean'], 0)
        
    df_mdm.to_csv(f"{PROCESSED_DIR}/processed_mdm.csv", index=False)

    # 5. Test Scores
    print("Processing Test Scores...")
    with open(f"{RAW_DIR}/track4_test_scores.json", 'r') as f:
        data = json.load(f)
    df_scores = pd.DataFrame(data)
    df_scores['school_id_clean'] = df_scores['school_id'].apply(normalize_school_id)
    df_scores['date_clean'] = pd.to_datetime(df_scores['date'], errors='coerce')
    df_scores['score_percentage_clean'] = df_scores.apply(normalize_test_score, axis=1)
    df_scores.to_csv(f"{PROCESSED_DIR}/processed_test_scores.csv", index=False)

    print("Pipeline completed successfully.")

if __name__ == "__main__":
    main()
