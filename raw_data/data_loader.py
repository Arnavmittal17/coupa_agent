import pandas as pd
import sqlite3
import re
import os
from datetime import datetime

def clean_name(name):
    """Cleans a string to be a valid SQLite table or column name."""
    name = str(name).strip()
    name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    name = re.sub(r'_+', '_', name)
    name = name.strip('_')
    return name

DATE_COLS_MAIN = [
    'REQ_INIT_DT',
    'LTST_FORM_1_STS_DT',
    'LTST_FORM_2_STS_DT',
    'LTST_FORM_3_STS_DT',
    'LTST_FORM_1_RJCTD_DT',
    'LTST_FORM_2_RJCTD_DT',
    'LTST_FORM_3_RJCTD_DT',
]

def parse_date(val):
    """Parse M/D/YYYY or YYYY-MM-DD into YYYY-MM-DD string. Returns None if unparseable."""
    if pd.isna(val) or str(val).strip() == '':
        return None
    val = str(val).strip()
    for fmt in ('%m/%d/%Y', '%Y-%m-%d', '%m-%d-%Y', '%d/%m/%Y'):
        try:
            return datetime.strptime(val, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    return None  # Unrecognised format → NULL in DB

def tat_days(date_end, date_start):
    """Return integer days between two YYYY-MM-DD strings, or None if either is None."""
    if date_end is None or date_start is None:
        return None
    try:
        d1 = datetime.strptime(date_start, '%Y-%m-%d')
        d2 = datetime.strptime(date_end, '%Y-%m-%d')
        diff = (d2 - d1).days
        return diff if diff >= 0 else None
    except Exception:
        return None

def load_maintable(csv_path, db_conn):
    """Loads coupa_dummy_data.csv into 'maintable', normalising dates and adding TAT columns."""
    print(f"Loading '{csv_path}' into table 'maintable'...")
    try:
        df = pd.read_csv(csv_path)

        # Clean column names
        df.columns = [clean_name(col) for col in df.columns]

        # Normalise date columns to YYYY-MM-DD
        for col in DATE_COLS_MAIN:
            if col in df.columns:
                df[col] = df[col].apply(parse_date)

        # Compute pre-built TAT columns (integer days)
        # TAT_FORM1: Form 1 duration — from request initiation to Form 1 completion
        df['TAT_FORM1'] = df.apply(
            lambda r: tat_days(r.get('LTST_FORM_1_STS_DT'), r.get('REQ_INIT_DT'))
            if pd.notna(r.get('LTST_FORM_1_STS_DT')) else None,
            axis=1
        )

        # TAT_FORM2: Form 2 duration — from Form 1 completion to Form 2 completion
        df['TAT_FORM2'] = df.apply(
            lambda r: tat_days(r.get('LTST_FORM_2_STS_DT'), r.get('LTST_FORM_1_STS_DT'))
            if pd.notna(r.get('LTST_FORM_2_STS_DT')) and pd.notna(r.get('LTST_FORM_1_STS_DT')) else None,
            axis=1
        )

        # TAT_FORM3: Form 3 duration — from Form 2 completion to Form 3 completion
        df['TAT_FORM3'] = df.apply(
            lambda r: tat_days(r.get('LTST_FORM_3_STS_DT'), r.get('LTST_FORM_2_STS_DT'))
            if pd.notna(r.get('LTST_FORM_3_STS_DT')) and pd.notna(r.get('LTST_FORM_2_STS_DT')) else None,
            axis=1
        )

        # TAT_OVERALL: Total duration — from request initiation to Form 3 completion
        # Only for fully Completed records
        df['TAT_OVERALL'] = df.apply(
            lambda r: tat_days(r.get('LTST_FORM_3_STS_DT'), r.get('REQ_INIT_DT'))
            if r.get('REQ_OVRL_STS_NM') == 'Completed'
               and pd.notna(r.get('LTST_FORM_3_STS_DT'))
               and pd.notna(r.get('REQ_INIT_DT')) else None,
            axis=1
        )

        df.to_sql('maintable', db_conn, if_exists='replace', index=False)
        non_null_tat = df['TAT_OVERALL'].notna().sum()
        print(f"  - Loaded 'maintable' with {len(df)} rows. TAT_OVERALL populated for {non_null_tat} completed records.")

    except Exception as e:
        print(f"Error loading {csv_path}: {e}")
        raise

def load_csp(csv_path, db_conn):
    """Loads coupa_supplier_portal.csv into 'csp'. Drops Supplier Information Status."""
    print(f"Loading '{csv_path}' into table 'csp'...")
    try:
        df = pd.read_csv(csv_path)
        df = df.drop(columns=['Supplier Information Status'], errors='ignore')
        df.columns = [clean_name(col) for col in df.columns]
        df.to_sql('csp', db_conn, if_exists='replace', index=False)
        print(f"  - Loaded 'csp' with {len(df)} rows.")
    except Exception as e:
        print(f"Error loading {csv_path}: {e}")
        raise

if __name__ == "__main__":
    base = os.path.dirname(os.path.abspath(__file__))
    db_path  = os.path.join(base, '..', 'coupa_data.db')
    file_main = os.path.join(base, 'coupa_dummy_data.csv')
    file_csp  = os.path.join(base, 'coupa_supplier_portal.csv')

    conn = sqlite3.connect(db_path)
    load_maintable(file_main, conn)
    load_csp(file_csp, conn)
    conn.close()
    print("Done — maintable and csp updated in coupa_data.db")
