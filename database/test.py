import json
import os
from pymongo import MongoClient
import pandas as pd

mongo_uri = "mongodb://localhost:27017/"
db_name = "VEC"

client = MongoClient(mongo_uri)
db = client[db_name]


def insert_academic_calender():

    collection = db['academic_calender']  
    with open("/Velammal-Engineering-College-Backend/docs/academic_calender.json", "r",encoding="utf-8") as file:
        documents = json.load(file)
        collection.insert_many(documents)

    print("academic calender inserted successfully.")


def insert_about_placement():

    collection = db['about_placement']  
    with open("/Velammal-Engineering-College-Backend/docs/about_placement.json", "r",encoding="utf-8") as file:
        documents = json.load(file)
        collection.insert_many(documents)

    print("about placement inserted successfully.")

def insert_about_us():

    collection = db['about_us']  
    with open("/Velammal-Engineering-College-Backend/docs/about_us.json", "r",encoding="utf-8") as file:
        documents = json.load(file)
        collection.insert_many(documents)

    print("about_us documents inserted successfully.\n")


def insert_organization_chart():

    collection = db['organization_chart']  
    with open("/Velammal-Engineering-College-Backend/docs/organization_chart.json", "r",encoding="utf-8") as file:
        documents = json.load(file)
        collection.insert_one(documents)

    print("organization chart json documents inserted successfully.\n")


def insert_admission():

    collection = db['admission']  
    with open("/Velammal-Engineering-College-Backend/docs/admission.json", "r",encoding="utf-8") as file:
        documents = json.load(file)
        collection.insert_one(documents)

    print("admission json documents inserted successfully.\n")



insert_academic_calender()
insert_about_us()
insert_about_placement()
insert_organization_chart()
insert_admission()