import json
import os
from pymongo import MongoClient

mongo_uri = "mongodb://localhost:27017/"
db_name = "VEC"

client = MongoClient(mongo_uri)
db = client[db_name]


def insert_alumni_data():
    collection = db['alumni']
    with open("/Velammal-Engineering-College-Backend/docs/alumni.json","r",encoding="utf-8") as file:
        documents = json.load(file)
        collection.insert_many(documents)
    
    print("Inserted Alumni data. \n")


insert_alumni_data()