import pandas as pd
import pymongo
import bcrypt
import requests
import os
import imghdr
import re

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["VEC"]
collection = db["student_database"]

storage_dir = r"D:\Velammal-Engineering-College-Backend\docs"
image_dir = r"D:\Velammal-Engineering-College-Backend\static\student_database"
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
    session = requests.Session()

    download_url = f"https://drive.google.com/uc?id={file_id}&export=download"
    
    print(f"🔍 Trying to download image for {reg_number}")
    print(f"🔗 Download URL: {download_url}")
    
    response = session.get(download_url, stream=True)

    print(f"📄 Response Headers: {response.headers}")
    
    if "text/html" in response.headers.get("Content-Type", ""):
        print(f"⚠️ Received an HTML response instead of an image for {reg_number}. Saving debug file.")
        debug_path = os.path.join(storage_dir, f"debug_{reg_number}.html")
        with open(debug_path, "wb") as debug_file:
            debug_file.write(response.content)
        print(f"🔎 Check {debug_path} for possible Google Drive warning page.")
        
        # Check for a confirmation link
        match = re.search(r'href="(/uc\?export=download[^"]+)', response.text)
        if match:
            confirm_url = "https://drive.google.com" + match.group(1).replace("&amp;", "&")
            print(f"🔁 Following confirmation URL: {confirm_url}")
            response = session.get(confirm_url, stream=True)

    # Check if the response is now an image
    if response.status_code == 200 and "image" in response.headers.get("Content-Type", ""):
        with open(image_path, "wb") as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)

        if imghdr.what(image_path) not in ["jpeg", "jpg"]:
            print(f"❌ Invalid image format for {reg_number}. Removing corrupt file.")
            os.remove(image_path)
            return None

        print(f"✅ Downloaded profile photo for {reg_number}")
        return f"/static/images/student_profile_photos/{reg_number}.jpeg"
    else:
        print(f"❌ Failed to download image for {reg_number} (Invalid content type: {response.headers.get('Content-Type')})")
        return None

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

students = []
for _, row in df.iterrows():
    reg_number = str(row["Registration Number (Example : 11322207000)"])
    
    student_doc = {
        "name": row["Name (Example : JOHN DOE K)"],
        "registration_number": reg_number,
        "password": hash_password(str(row["Password (Format  DD-MM-YYYY)"])),
        "admin_number": row["Admission Number (Example : 22VEC-000)"],
        "room_number": row["Room Number (Current)"],
        "department": row["Department"],
        "gender": row["Gender"],
        "phone_number_student": row["Student Phone Number (Example : 9876543210)"],
        "city": row["City"],
        "foodtype": row["Food Type"],
        "year": int(row["Year of Studying"]),
        "profile_photo_path": set_path(row.get("Student Image", ""), reg_number),
        "block_name": row["Block Name"],
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
