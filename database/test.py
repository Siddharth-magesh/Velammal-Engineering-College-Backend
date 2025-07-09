import json
import os
from pymongo import MongoClient
import pandas as pd

mongo_uri = "mongodb://localhost:27017/"
db_name = "NEW_VEC"

client = MongoClient(mongo_uri)
db = client[db_name]

department_mapping1 = {
    "Artificial Intelligence and Data Science (AI&DS)": "001",
    "Automobile Engineering (AUTO)": "002",
    "Chemistry": "003",
    "Civil Engineering (CIVIL)": "004",
    "Computer Science & Engineering (CSE)": "005",
    "Computer Science and Engineering (CYBER SECURITY)": "006",
    "Electrical & Electronics Engineering (EEE)": "007",
    "Electronics & Instrumentation Engineering (EIE)": "008",
    "Electronics and Communication Engineering (ECE)": "009",
    "English": "010",
    "Information Technology (IT)": "011",
    "Mathematics": "012",
    "Mechancial Engineering (MECH)": "013",
    "Tamil": "014",
    "Physics": "015",
    "Master Of Computer Science": "016",
    "Master of Business Admin": "017",
    "Physical Education":"020",
    "Placement":"021"
}

def insert_faculty_data(folder_path):
    department_name=None
    with open(r"/Velammal-Engineering-College-Backend/docs/prev_faculty.json","r",encoding="utf-8") as file:
        data=json.load(file)
    try:
        collection = db['faculty_data']
        if not os.path.exists(folder_path):
            print(f"Error: Folder path '{folder_path}' does not exist. \n")
            return

        for file_name in os.listdir(folder_path):
            
            if file_name.endswith(".xlsx"):
                file_path = os.path.join(folder_path, file_name)

                dept_id = os.path.splitext(file_name)[0]

                try:
                    df = pd.read_excel(file_path)
                except Exception as e:
                    print(f"Error reading Excel file '{file_name}': {e}\n")
                    continue
                required_columns = [
                    "Name", "Designation", "Photo", "Google Scholar Profile",
                    "Research Gate", "Orchid Profile", "Publon Profile",
                    "Scopus Author Profile", "LinkedIn Profile", "unique_id"
                ]
                missing_columns = [col for col in required_columns if col not in df.columns]
                if missing_columns:
                    print(f"Error: Missing columns in '{file_name}': {missing_columns}\n")
                    continue 

                faculty_list = []
                for index, row in df.iterrows():
                    try:
                        faculty_data = {
                            "name": row["Name"],
                            "designation": row["Designation"],
                            "photo": row["Photo"],
                            "profiles": {
                                "google_scholar": row["Google Scholar Profile"],
                                "research_gate": row["Research Gate"],
                                "orchid": row["Orchid Profile"],
                                "publon": row["Publon Profile"],
                                "scopus": row["Scopus Author Profile"],
                                "linkedin": row["LinkedIn Profile"]
                            },
                            "unique_id": row["unique_id"]
                        }
                        faculty_list.append(faculty_data)
                    except Exception as e:
                        print(f"Error processing row {index} in '{file_name}': {e}\n")
                for name, id in department_mapping1.items() :
                    if id==dept_id:
                        department_name=name
                        
                        department_document = {
                            "department_name": department_name,
                            "dept_id": dept_id,
                            "previous_faculty_pdf_path":data.get(dept_id),
                            "faculty_members": faculty_list
                        }
                if faculty_list:
                    try:
                        collection.insert_one(department_document)
                    except Exception as e:
                        print(f"Error inserting document for '{dept_id}' into MongoDB: {e}\n")
                else:
                    print(f"No valid faculty data to insert for '{file_name}'.\n")
    except Exception as e:
        print(f"Unexpected error: {e}\n")

    print("Faculty Data Insertion Done\n")
    return

insert_faculty_data(folder_path=r"/Velammal-Engineering-College-Backend/docs/STAFF-DATA/")
