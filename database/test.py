import json
import os
from pymongo import MongoClient

mongo_uri = "mongodb://localhost:27017/"
db_name = "VEC"

client = MongoClient(mongo_uri)
db = client[db_name]

def insert_department_research_data():
    collection = db['research_data']
    
    folder_path = "/Velammal-Engineering-College-Backend/docs/RESEARCH-DATA"
    
    for file_name in os.listdir(folder_path):
        if file_name.endswith(".json"):
            file_path = os.path.join(folder_path, file_name)
            
            try:
                with open(file_path, "r", encoding='utf-8') as file:
                    document = json.load(file)
                    collection.insert_one(document)
            except Exception as e:
                print(f"Error inserting {file_name}: {e}")
    
    print("All available Department Research documents inserted successfully.")
insert_department_research_data()