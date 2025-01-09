import os
import json
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['VEC1']
collection = db['research_data']

department_mapping = {
    "Artificial Intelligence and Data Science": "001",
    "Automobile Engineering": "002",
    "Chemistry": "003",
    "Civil Engineering": "004",
    "Computer Science & Engineering": "005",
    "Computer Science and Engineering (CYBER SECURITY)": "006",
    "Electrical & Electronics Engineering": "007",
    "Electronics & Instrumentation Engineering": "008",
    "Electronics and Communication Engineering": "009",
    "English": "010",
    "Information Technology": "011",
    "Mathematics": "012",
    "Mechancial Engineering": "013",
    "Physical Education": "014",
    "Physics": "015"
}

def upload_research_data(folder_path):
    for filename in os.listdir(folder_path):
        if filename.endswith('.json'):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'r') as file:
                try:
                    data = json.load(file)
                    dept_id = filename.split('.')[0]
                    if dept_id not in department_mapping.values():
                        print(f"Skipping unrecognized dept_id: {dept_id}")
                        continue

                    collection.insert_one({"dept_id": dept_id, "data": data})
                    print(f"✅ Successfully inserted data for {dept_id}")

                except json.JSONDecodeError as e:
                    print(f"❌ Error decoding JSON from {filename}: {e}")
                except Exception as e:
                    print(f"❌ Error processing {filename}: {e}")

folder_path = r'D:\Velammal-Engineering-College-Backend\docs\RESEARCH-DATA'
upload_research_data(folder_path)