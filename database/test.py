import json
from pymongo import MongoClient
import os

MONGO_URI = "mongodb://localhost:27017"
DATABASE_NAME = "your_database" 
COLLECTION_NAME = "your_collection"

json_file_path = "structured_data2.json" 

client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

# Read JSON file
with open(json_file_path, "r", encoding="utf-8") as file:
    data = json.load(file)  # Load JSON data

# Insert into MongoDB
if isinstance(data, list):  
    # If the JSON file contains a list of documents
    collection.insert_many(data)
else:
    # If the JSON file contains a single document
    collection.insert_one(data)

print("JSON data inserted into MongoDB successfully!")

# Close the MongoDB connection
client.close()

def insert_department_research_data():
    collection = db['department_research_data']
    
    folder_path = "/Velammal-Engineering-College-Backend/docs/new_research_data"
    
    for file_name in os.listdir(folder_path):
        if file_name.endswith(".json"):
            file_path = os.path.join(folder_path, file_name)
            
            try:
                with open(file_path, "r") as file:
                    document = json.load(file)
                    collection.insert_one(document)
                    print(f"Inserted: {file_name}")
            except Exception as e:
                print(f"Error inserting {file_name}: {e}")
    
    print("All available documents inserted successfully.")

insert_department_research_data()