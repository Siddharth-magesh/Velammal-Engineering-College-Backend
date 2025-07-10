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

def insert_placement_data():

    collection = db['placements_data']  
    with open("/root/Velammal-Engineering-College-Backend/docs/placements_data.json", "r",encoding="utf-8") as file:
        documents = json.load(file)
        collection.insert_many(documents)

    print("placement documents inserted successfully.")

insert_placement_data()