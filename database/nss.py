from pymongo import MongoClient
import json

mongo_uri = "mongodb://localhost:27017/"
db_name = "VEC"
client = MongoClient(mongo_uri)
db = client[db_name]

def insert_nss_podcast():
    collection= db['nsspodcast']
    with open ("/Velammal-Engineering-College-Backend/docs/nsspodcast.json","r") as file:
        documents= json.load(file)
        collection.insert_many(documents)
    print("NSS_Podcast documents inserted successfully")

def insert_nss_home_data():
    collection = db["nsshome"]
    with open("/Velammal-Engineering-College-Backend/docs/nss_home.json", "r") as file:
        documents = json.load(file)
        collection.insert_one(documents)

    print("NSS home data inserted successfully.")

def insert_nss_events():
    collection = db["nssgallery"]
    with open("/Velammal-Engineering-College-Backend/docs/nss_gallery.json", "r") as file:
        documents = json.load(file)
        collection.insert_many(documents)

    print("NSS gallery data inserted successfully.")

def insert_nss_faculty_data():
    collection = db["nss_faculty"]
    with open("/Velammal-Engineering-College-Backend/docs/nss_faculty.json", "r") as file:
        documents = json.load(file)
        collection.insert_one(documents)

    print("NSS faculty data inserted successfully.")

insert_nss_podcast()
insert_nss_home_data()
insert_nss_events()
insert_nss_faculty_data()