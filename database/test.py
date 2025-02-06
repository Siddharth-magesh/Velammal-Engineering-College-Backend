from pymongo import MongoClient
import json

mongo_uri = "mongodb://localhost:27017/"
db_name = "VEC"
collection_name = "staff_details"

client = MongoClient(mongo_uri)
db = client[db_name]
collection = db[collection_name]

def insert_sports_Zonal_results():
    collection = db["sports_data"]
    with open("/Velammal-Engineering-College-Backend/docs/sports_zonal.json", "r") as file:
        documents = json.load(file)
        collection.insert_many(documents)

    print("Sports Zonal data inserted successfully.")
    
def insert_sports_Zonal_images():
    collection = db["sports_data"]
    with open("/Velammal-Engineering-College-Backend/docs/zonal_images.json", "r") as file:
        documents = json.load(file)
        collection.insert_many(documents)

    print("Sports Zonal images data inserted successfully.")

def insert_sports_faculty_data():
    collection = db["sports_data"]
    with open("/Velammal-Engineering-College-Backend/docs/sports_faculty.json", "r") as file:
        documents = json.load(file)
        collection.insert_one(documents)

    print("sports faculty data inserted successfully.")

#insert_sports_Zonal_results()
#insert_sports_Zonal_images()
insert_sports_faculty_data()