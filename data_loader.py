import pandas as pd
import sqlite3
import re
import os

def clean_name(name):
    """Cleans a string to be a valid SQLite table or column name."""
    name = str(name).strip()
    name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    name = re.sub(r'_+', '_', name)
    name = name.strip('_')
    return name

def load_excel_sheet_to_sqlite(excel_path, db_conn, sheet_name, table_name=None):
    """Loads a specific sheet from an Excel file into a SQLite database."""
    print(f"Loading sheet '{sheet_name}' from {excel_path}...")
    try:
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
        
        # Clean column names
        df.columns = [clean_name(col) for col in df.columns]
        
        # Determine table name
        if not table_name:
            table_name = clean_name(sheet_name).lower()
            
        # Save to SQLite
        df.to_sql(table_name, db_conn, if_exists='replace', index=False)
        print(f"  - Loaded into table '{table_name}' with {len(df)} rows.")
        
    except Exception as e:
        print(f"Error loading sheet {sheet_name} from {excel_path}: {e}")

if __name__ == "__main__":
    db_path = "coupa_data.db"
    
    # Remove existing db if it exists
    if os.path.exists(db_path):
        os.remove(db_path)
        
    conn = sqlite3.connect(db_path)
    
    file1 = 'CoupaPOC_DummyData.xlsx'
    file2 = 'Coupa_Master_Test_Data.xlsx'
    
    # Only load 'Annotations' sheet from CoupaPOC_DummyData.xlsx as requested by user
    load_excel_sheet_to_sqlite(file1, conn, sheet_name='Annotations', table_name='annotations')
    
    # Load all sheets from Coupa_Master_Test_Data.xlsx except its 'Annotations' sheet
    print(f"Inspecting {file2}...")
    try:
        xl2 = pd.ExcelFile(file2)
        for sheet in xl2.sheet_names:
            if sheet.lower() != 'annotations': # We already have the annotations from file1
                load_excel_sheet_to_sqlite(file2, conn, sheet_name=sheet)
    except Exception as e:
        print(f"Error reading {file2}: {e}")
    
    conn.close()
    print("Data loaded successfully into coupa_data.db")
