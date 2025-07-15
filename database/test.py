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

def insert_about_us():

    collection = db['about_us']  
    with open("/root/Velammal-Engineering-College-Backend/docs/about_us.json", "r",encoding="utf-8") as file:
        documents = json.load(file)
        collection.insert_many(documents)

    print("about_us documents inserted successfully.\n")


def insert_organization_chart():

    collection = db['organization_chart']  
    with open("/root/Velammal-Engineering-College-Backend/docs/organization_chart.json", "r",encoding="utf-8") as file:
        documents = json.load(file)
        collection.insert_one(documents)

    print("organization chart json documents inserted successfully.\n")



def insert_hostel_menu():

    collection = db['hostel_menu']  
    with open("/root/Velammal-Engineering-College-Backend/docs/hostel_menu.json", "r",encoding="utf-8") as file:
        documents = json.load(file)
        collection.insert_many(documents)

    print("hostel_menu documents inserted successfully.\n")

def insert_help_desk():

    collection = db['help_desk']  
    with open("/root/Velammal-Engineering-College-Backend/docs/help_desk.json", "r",encoding="utf-8") as file:
        documents = json.load(file)
        collection.insert_many(documents)

    print("help_desk documents inserted successfully.\n")
insert_about_us()
insert_organization_chart()
insert_hostel_menu()
insert_help_desk()

# insert_acadamic_research()

def add_hostel_student_database():
    collection = db["student_database"]
    storage_dir = r"/root/Velammal-Engineering-College-Backend/docs/CSV"
    image_dir = r"/root/Velammal-Engineering-College-Backend/static/student_database"
    os.makedirs(storage_dir, exist_ok=True)  
    os.makedirs(image_dir, exist_ok=True)  

    csv_file_path = os.path.join(storage_dir, "VEC_Hostel_Students.csv")

    df = pd.read_csv(csv_file_path)
    df = df.head(1)

    df.columns = df.columns.str.strip()

    def extract_drive_file_id(drive_link):
        if isinstance(drive_link, str) and "drive.google.com" in drive_link:
            if "id=" in drive_link:
                return drive_link.split("id=")[-1]
            elif "/d/" in drive_link:
                return drive_link.split("/d/")[1].split("/")[0]
        return None

    def set_path(drive_link, reg_number):
        file_id = extract_drive_file_id(drive_link)
        if not file_id:
            print(f"⚠️ Invalid Google Drive link for {reg_number}: {drive_link}")
            return None

        image_path = os.path.join(image_dir, f"{reg_number}.jpeg")
        download_url = f"https://drive.google.com/uc?id={file_id}"

        try:
            response = requests.get(download_url, stream=True)
            if response.status_code == 200:
                with open(image_path, "wb") as file:
                    for chunk in response.iter_content(1024):
                        file.write(chunk)
                print(f"✅ Downloaded profile photo for {reg_number}")
                return f"/static/images/student_profile_photos/{reg_number}.jpeg"
            else:
                print(f"❌ Failed to download image for {reg_number} (HTTP {response.status_code})")
                return None
        except Exception as e:
            print(f"❌ Error downloading image for {reg_number}: {e}")
            return None

    def hash_password(password):
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def format_food_type(food_type):
        return "Non-Veg" if food_type == "Non-Vegetarian" else "Veg"

    def set_year(year, department):
        if department == 'MBA':
            if year == 1:
                return 5
            elif year == 2:
                return 6
        elif department == 'MECSE':
            if year == 1:
                return 7
            elif year == 2:
                return 8
        return year
        
    students = []
    for _, row in df.iterrows():
        reg_number = str(row.get("Registration Number (Example : 11322207000)", ""))

        student_doc = {
            "name": row.get("Name (Example : JOHN DOE K)", ""),
            "registration_number": reg_number,
            "password": hash_password(str(row.get("Password (Format  DD-MM-YYYY)", ""))),
            "admin_number": row.get("Admission Number (Example : 22VEC-000)", ""),
            "room_number": row.get("Room Number (Current)", ""),
            "department": row.get("Department", ""),
            "gender": row.get("Gender", ""),
            "phone_number_student": row.get("Student Phone Number (Example : 9876543210)", ""),
            "city": row.get("City", ""),
            "foodtype": format_food_type(row.get("Food Type", "")),
            "year": set_year(int(row.get("Year of Studying", 0) or 0), row.get("Department", "")),
            "profile_photo_path": set_path(row.get("Student Image", ""), reg_number),
            "block_name": row.get("Block Name", ""),
            "late_count": 0,
            "QR_path": f"/static/student_barcode/{reg_number}.png",
            "edit_status": "Approved",
            "changes": []
        }
        students.append(student_doc)

    if students:
        collection.insert_many(students)
        print(f"✅ Successfully inserted {len(students)} students into MongoDB!")
    else:
        print("⚠️ No student data to insert.")
