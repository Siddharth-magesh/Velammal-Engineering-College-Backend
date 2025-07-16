import json
import os
from pymongo import MongoClient
import pandas as pd
import bcrypt
import requests

mongo_uri = "mongodb://localhost:27017/"
db_name = "VEC"

client = MongoClient(mongo_uri)
db = client[db_name]


def insert_iqac_data():
    collection = db['IQAC']
    with open("/root/Velammal-Engineering-College-Backend/docs/IQAC.json","r",encoding="utf-8") as file:
        documents = json.load(file)
        collection.insert_many(documents)
    
    print("inserted IQAC data")


insert_iqac_data()