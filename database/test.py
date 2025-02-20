import os
import json
import re
import pandas as pd

department_mapping1 = {
    "001": "Artificial Intelligence and Data Science (AI&DS)",
    "002": "Automobile Engineering (AUTO)",
    "003": "Chemistry",
    "004": "Civil Engineering (CIVIL)",
    "005": "Computer Science & Engineering (CSE)",
    "006": "Computer Science and Engineering (CYBER SECURITY)",
    "007": "Electrical & Electronics Engineering (EEE)",
    "008": "Electronics & Instrumentation Engineering (EIE)",
    "009": "Electronics and Communication Engineering (ECE)",
    "010": "English",
    "011": "Information Technology (IT)",
    "012": "Mathematics",
    "013": "Mechancial Engineering (MECH)",
    "014": "Physical Education",
    "015": "Physics"
}

parent_folder = "D:\Velammal-Engineering-College-Backend\docs\depts_fol"

def convert_df_to_json(df):
    df = df.astype(str)
    return {col: df[col].dropna().tolist() for col in df.columns}

def format_sheet_name(sheet_name):
    return sheet_name.lower().replace(" ", "_")

def extract_year_from_filename(filename):
    match = re.search(r"(\d{4}-\d{2})", filename)
    return match.group(1) if match else "Unknown"

for department_id in os.listdir(parent_folder):
    department_path = os.path.join(parent_folder, department_id)
    
    if not os.path.isdir(department_path) or department_id not in department_mapping1:
        continue

    department_name = department_mapping1[department_id]
    
    research_data = []

    for file in os.listdir(department_path):
        if file.endswith(".xlsx") or file.endswith(".xls"):
            file_path = os.path.join(department_path, file)
            
            year = extract_year_from_filename(file)
            xls = pd.ExcelFile(file_path)
            
            data_dict = {}

            for sheet_name in xls.sheet_names:
                formatted_sheet_name = format_sheet_name(sheet_name)
                df = pd.read_excel(xls, sheet_name=sheet_name)
                data_dict[formatted_sheet_name] = convert_df_to_json(df)

            research_data.append({
                "year": year,
                "data": data_dict
            })

    output_json = {
        "department_id": department_id,
        "department_name": department_name,
        "research_data": research_data
    }
    output_file = os.path.join(parent_folder, f"{department_id}.json")
    with open(output_file, "w", encoding="utf-8") as json_file:
        json.dump(output_json, json_file, indent=4)

    print(f"✅ Processed {department_name} ({department_id}) → {output_file}")

print("🎉 All department files processed successfully!")