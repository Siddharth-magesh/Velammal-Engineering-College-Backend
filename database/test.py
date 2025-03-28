import json
import os
from pymongo import MongoClient

mongo_uri = "mongodb://localhost:27017/"
db_name = "NEW_VEC"

client = MongoClient(mongo_uri)
db = client[db_name]

def insert_overall_patent():
    collection = db['overall_patent']
    with open("/Velammal-Engineering-College-Backend/docs/overall_patent.json","r",encoding="utf-8") as file:
        documents = json.load(file)
        collection.insert_many(documents)
    
    print("Inserted overall patent.\n")


insert_overall_patent()