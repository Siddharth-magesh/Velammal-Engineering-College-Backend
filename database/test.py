import json
import os
from pymongo import MongoClient
import pandas as pd

mongo_uri = "mongodb://localhost:27017/"
db_name = "VEC"

client = MongoClient(mongo_uri)
db = client[db_name]


def insert_landing_page_details():

    collection = db['landing_page_details']  
    with open("/Velammal-Engineering-College-Backend/docs/landing_page_details.json", "r",encoding="utf-8") as file:
        documents = json.load(file)
        collection.insert_one(documents)

    print("insert_landing_page_details documents inserted successfully.\n")

insert_landing_page_details()