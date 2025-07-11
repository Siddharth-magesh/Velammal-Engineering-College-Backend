import json
import os
from pymongo import MongoClient
import pandas as pd

mongo_uri = "mongodb://localhost:27017/"
db_name = "VEC"

client = MongoClient(mongo_uri)
db = client[db_name]


def insert_placement_data():

    collection = db['placements_data']  
    with open("/root/Velammal-Engineering-College-Backend/docs/placements_data.json", "r",encoding="utf-8") as file:
        documents = json.load(file)
        collection.insert_many(documents)

    print("placement documents inserted successfully.")

def insert_army_data():
    collection = db['army']
    with open("/root/Velammal-Engineering-College-Backend/docs/ncc_army.json", "r",encoding="utf-8") as file:
        documents = json.load(file)
        collection.insert_many(documents)
    print("armydocuments inserted successfully.")

insert_army_data()

insert_placement_data()