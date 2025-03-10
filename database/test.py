import json
from pymongo import MongoClient

mongo_uri = "mongodb://localhost:27017/"
db_name = "VEC"

client = MongoClient(mongo_uri)
db = client[db_name]

def insert_incubation_data():
    collection= db['incubation']
    with open ("/Velammal-Engineering-College-Backend/docs/incubation.json","r",encoding="utf-8") as file:
        documents= json.load(file)
        collection.insert_many(documents)
    print("Incubation documents inserted successfully")

def insert_army_data():
    collection = db['army']
    with open("/Velammal-Engineering-College-Backend/docs/ncc_army.json", "r",encoding="utf-8") as file:
        documents = json.load(file)
        collection.insert_many(documents)
    print("armydocuments inserted successfully.")

def insert_navy_data():
    collection = db['navy']
    with open("/Velammal-Engineering-College-Backend/docs/navy.json", "r",encoding="utf-8") as file:
        documents = json.load(file)
        collection.insert_many(documents)
    print("navy documents inserted successfully.")

insert_incubation_data()
insert_army_data()
insert_navy_data()