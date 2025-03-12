import os
import requests
import pandas as pd
from pymongo import MongoClient
from docx import Document
import json
import shutil
import bcrypt
import re

mongo_uri = "mongodb://localhost:27017/"
db_name = "VEC"
collection_name = "staff_details"

file_path = r"/root/Velammal-Engineering-College-Backend/docs/VEC_Faculty_Details.csv"
photo_base_dir = r"/root/Velammal-Engineering-College-Backend/static/temp_photos/"
base_save_dir = r"/root/Velammal-Engineering-College-Backend/static/staff_scholar_details/"

client = MongoClient(mongo_uri)
db = client[db_name]
collection = db[collection_name]

columns_to_keep = [
    "Name",
    "Initial or Surname",
    "Designation",
    "Joined in",
    "Department Name",
    "Mail ID",
    "Photo",
    "Google Scholar Profile",
    "Research Gate",
    "Orchid Profile",
    "Publon Profile",
    "Scopus Author Profile",
    "LinkedIn Profile",
    "Professional Membership",
    "Sponsored Projects",
    "Patent Granted",
    "Patent Published",
    "Patent Filed",
    "Journal Publications",
    "Conference Publications",
    "Book / Book Chapter Published",
    "Seminar / Workshop / Guest Lectures Delivered",
    "Seminar / Workshop / Guest Lectures Attended",
    "Conference / Seminar / Workshop / Guest Lectures Organized",
    "PHD Produced",
    "PHD Pursuing",
    "Upload Your Excel File Here"
]

department_mapping = {
    "Artificial Intelligence and Data Science": "001",
    "Automobile Engineering": "002",
    "Chemistry": "003",
    "Civil Engineering": "004",
    "Computer Science & Engineering": "005",
    "Computer Science and Engineering (CYBER SECURITY)": "006",
    "Electrical & Electronics Engineering": "007",
    "Electronics & Instrumentation Engineering": "008",
    "Electronics and Communication Engineering": "009",
    "English": "010",
    "Information Technology": "011",
    "Mathematics": "012",
    "Mechancial Engineering": "013",
    "Tamil": "014",
    "Physics": "015"
}

department_mapping1 = {
    "Artificial Intelligence and Data Science (AI&DS)": "001",
    "Automobile Engineering (AUTO)": "002",
    "Chemistry": "003",
    "Civil Engineering (CIVIL)": "004",
    "Computer Science & Engineering (CSE)": "005",
    "Computer Science and Engineering (CYBER SECURITY)": "006",
    "Electrical & Electronics Engineering (EEE)": "007",
    "Electronics & Instrumentation Engineering (EIE)": "008",
    "Electronics and Communication Engineering (ECE)": "009",
    "English": "010",
    "Information Technology (IT)": "011",
    "Mathematics": "012",
    "Mechancial Engineering (MECH)": "013",
    "Tamil": "014",
    "Physics": "015"
}

designation_mapping = {
    "Professor & Head": "01",
    "Professor": "02",
    "Associate Professor": "03",
    "Assistant Professor": "04"
}

try:
    df = pd.read_csv(file_path)
except FileNotFoundError:
    print(f"File not found at {file_path}. Please check the path.")
    exit()

df = df[columns_to_keep]

def generate_unique_id(index, department, designation):
    department_id = department_mapping.get(department, "000")
    designation_id = designation_mapping.get(designation, "00") 
    unique_id = str(index + 1).zfill(3)
    return f"VEC-{department_id}-{designation_id}-{unique_id}"


#df = df.head(1) #Remove this line to deactivate Test settings

df['unique_id'] = [
    generate_unique_id(i, df.at[i, 'Department Name'], df.at[i, 'Designation'])
    for i in range(len(df))
]

def download_image(
        unique_id, 
        photo_url, 
        target_base_dir,
        save_base_dir
):
    if not photo_url or not isinstance(photo_url, str):
        return None
    
    file_name = f"{unique_id}.jpg"
    temp_save_dir = os.path.join(photo_base_dir, unique_id)
    os.makedirs(temp_save_dir, exist_ok=True)
    temp_file_path = os.path.join(temp_save_dir, file_name)

    try:
        if "drive.google.com" in photo_url:
            file_id = photo_url.split("id=")[-1]
            photo_url = f"https://drive.google.com/uc?id={file_id}"
        
        response = requests.get(photo_url, stream=True)
        if response.status_code == 200:
            with open(temp_file_path, "wb") as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)

            parts = unique_id.split('-')
            if len(parts) >= 3:
                department_code = parts[1]

                if department_code.isdigit() and 1 <= int(department_code) <= 15:
                    target_folder = os.path.join(target_base_dir, f"{int(department_code):03}")
                    os.makedirs(target_folder, exist_ok=True)

                    new_file_path = os.path.join(target_folder, file_name)
                    save_base_dir = os.path.join(save_base_dir, f"{int(department_code):03}")
                    save_file_path = os.path.join(save_base_dir, file_name)
                    shutil.move(temp_file_path, new_file_path)

                    return save_file_path
                else:
                    print(f"Skipping {unique_id} - Invalid department code {department_code}")
                    return None
            else:
                print(f"Skipping {unique_id} - Invalid format")
                return None
        else:
            print(f"Failed to download image for {unique_id}. URL: {photo_url}")
            return None
    except Exception as e:
        print(f"Error downloading image for {unique_id}: {e}")
        return None

target_base_dir = r"/root/Velammal-Engineering-College-Backend/static/images/profile_photos/"
save_base_dir = r"/root/Velammal-Engineering-college/static/images/profile_photos/"
df['Photo'] = df.apply(lambda row: download_image(row['unique_id'], row['Photo'], target_base_dir,save_base_dir), axis=1)


def extract_file_id(url):
    if url and isinstance(url, str) and "id=" in url:
        return url.split("id=")[-1]
    return None

def save_sheets_to_csv(file_path, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    excel_data = pd.ExcelFile(file_path)
    for sheet_name in excel_data.sheet_names:
        sheet_data = excel_data.parse(sheet_name) 
        csv_file = os.path.join(output_folder, f"{sheet_name}.csv") 
        sheet_data.to_csv(csv_file, index=False)

def download_and_save_faculty_data(unique_id, file_url):
    save_dir = os.path.join(base_save_dir, unique_id)
    os.makedirs(save_dir, exist_ok=True)

    file_id = extract_file_id(file_url)
    if not file_id:
        print(f"Invalid URL or missing file ID for {unique_id}. Skipping.")
        return

    download_url = f"https://drive.google.com/uc?id={file_id}"

    try:
        response = requests.get(download_url)
        if response.status_code == 200:
            excel_file_path = os.path.join(save_dir, f"{unique_id}_data.xlsx")
            with open(excel_file_path, 'wb') as f:
                f.write(response.content)
            save_sheets_to_csv(excel_file_path, save_dir)
        else:
            print(f"Failed to download file for {unique_id}. URL: {file_url}")
    except Exception as e:
        print(f"Error downloading or saving file for {unique_id}: {e}")

def insert_educational_qualifications_per_faculty(unique_id):
    folder_path = os.path.join(base_save_dir, unique_id)
    educational_file_path = os.path.join(folder_path, "EDUCATIONAL QUALIFICATION.csv")

    if not os.path.exists(educational_file_path):
        print(f"Educational qualification file not found for {unique_id}. Skipping.")
        return

    try:
        data = pd.read_csv(educational_file_path)
        educational_data = {
            "EDUCATIONAL_QUALIFICATION": data.to_dict(orient="records")
        }
        result = collection.update_one(
            {"unique_id": unique_id},
            {"$set": educational_data}
        )

        print(f"Update result: {result.modified_count} document(s) updated.")
        if result.modified_count > 0:
            print(f"Educational qualifications added for {unique_id}.")
        else:
            print(f"No changes made for {unique_id}.")
    except Exception as e:
        print(f"Error inserting educational qualifications for {unique_id}: {e}")

def insert_experience(unique_id):
    folder_path = os.path.join(base_save_dir, unique_id)
    experience_file_path = os.path.join(folder_path, "EXPERIENCE.csv")

    if not os.path.exists(experience_file_path):
        print(f"Experience file not found for {unique_id}. Skipping.")
        return

    try:
        data = pd.read_csv(experience_file_path)
        cleaned_columns = []
        for col in data.columns:
            cleaned_col = col.strip().replace(' ', '_')
            cleaned_columns.append(cleaned_col)
        data.columns = cleaned_columns

        experience_data = {
            "EXPERIENCE": data.to_dict(orient="records")
        }
        existing_document = collection.find_one({"unique_id": unique_id})
        
        if existing_document:
            result = collection.update_one(
                {"unique_id": unique_id},
                {"$set": experience_data}
            )
            print(f"Update result: {result.modified_count} document(s) updated.")
            if result.modified_count > 0:
                print(f"Experience data updated for {unique_id}.")
            else:
                print(f"No changes made for {unique_id}.")
        else:
            experience_data["unique_id"] = unique_id
            collection.insert_one(experience_data)
            print(f"Experience data added for {unique_id}.")
        
    except Exception as e:
        print(f"Error inserting experience data for {unique_id}: {e}")

def insert_projects(unique_id):
    folder_path = os.path.join(base_save_dir, unique_id)
    projects_file_path = os.path.join(folder_path, "PROJECTS.csv")

    if not os.path.exists(projects_file_path):
        print(f"Projects file not found for {unique_id}. Skipping.")
        return

    try:
        data = pd.read_csv(projects_file_path)
        cleaned_columns = []
        for col in data.columns:
            cleaned_col = col.strip().replace(' ', '_')
            cleaned_columns.append(cleaned_col)
        data.columns = cleaned_columns

        projects_data = {
            "PROJECTS": data.to_dict(orient="records")
        }
        existing_document = collection.find_one({"unique_id": unique_id})

        if existing_document:
            result = collection.update_one(
                {"unique_id": unique_id},
                {"$set": projects_data}
            )
            print(f"Update result: {result.modified_count} document(s) updated.")
            if result.modified_count > 0:
                print(f"Projects data updated for {unique_id}.")
            else:
                print(f"No changes made for {unique_id}.")
        else:
            projects_data["unique_id"] = unique_id
            collection.insert_one(projects_data)
            print(f"Projects data added for {unique_id}.")
        
    except Exception as e:
        print(f"Error inserting projects data for {unique_id}: {e}")

def insert_patents(unique_id):
    folder_path = os.path.join(base_save_dir, unique_id)
    patents_file_path = os.path.join(folder_path, "PATENTS.csv")

    if not os.path.exists(patents_file_path):
        print(f"Patents file not found for {unique_id}. Skipping.")
        return

    try:
        data = pd.read_csv(patents_file_path)
        cleaned_columns = []
        for col in data.columns:
            cleaned_col = col.strip().replace(' ', '_')
            cleaned_columns.append(cleaned_col)
        data.columns = cleaned_columns

        patents_data = {
            "PATENTS": data.to_dict(orient="records")
        }
        existing_document = collection.find_one({"unique_id": unique_id})

        if existing_document:
            result = collection.update_one(
                {"unique_id": unique_id},
                {"$set": patents_data}
            )
            print(f"Update result: {result.modified_count} document(s) updated.")
            if result.modified_count > 0:
                print(f"Patents data updated for {unique_id}.")
            else:
                print(f"No changes made for {unique_id}.")
        else:
            patents_data["unique_id"] = unique_id
            collection.insert_one(patents_data)
            print(f"Patents data added for {unique_id}.")
        
    except Exception as e:
        print(f"Error inserting patents data for {unique_id}: {e}")

def insert_journal_publications(unique_id):
    folder_path = os.path.join(base_save_dir, unique_id)
    journal_publications_file_path = os.path.join(folder_path, "JOURNAL-PUBLICATIONS.csv")

    if not os.path.exists(journal_publications_file_path):
        print(f"Journal publications file not found for {unique_id}. Skipping.")
        return

    try:
        data = pd.read_csv(journal_publications_file_path)
        cleaned_columns = []
        for col in data.columns:
            cleaned_col = col.strip().replace(' ', '_')
            cleaned_columns.append(cleaned_col)
        data.columns = cleaned_columns

        journal_publications_data = {
            "JOURNAL_PUBLICATIONS": data.to_dict(orient="records")
        }
        existing_document = collection.find_one({"unique_id": unique_id})

        if existing_document:
            result = collection.update_one(
                {"unique_id": unique_id},
                {"$set": journal_publications_data}
            )
            print(f"Update result: {result.modified_count} document(s) updated.")
            if result.modified_count > 0:
                print(f"Journal publications data updated for {unique_id}.")
            else:
                print(f"No changes made for {unique_id}.")
        else:
            journal_publications_data["unique_id"] = unique_id
            collection.insert_one(journal_publications_data)
            print(f"Journal publications data added for {unique_id}.")
        
    except Exception as e:
        print(f"Error inserting journal publications data for {unique_id}: {e}")

def insert_conference_publications(unique_id):
    folder_path = os.path.join(base_save_dir, unique_id)
    conference_publications_file_path = os.path.join(folder_path, "CONFERENCE-PUBLICATIONS.csv")

    if not os.path.exists(conference_publications_file_path):
        print(f"Conference publications file not found for {unique_id}. Skipping.")
        return

    try:
        data = pd.read_csv(conference_publications_file_path)
        cleaned_columns = []
        for col in data.columns:
            cleaned_col = col.strip().replace(' ', '_')
            cleaned_columns.append(cleaned_col)
        data.columns = cleaned_columns

        conference_publications_data = {
            "CONFERENCE_PUBLICATIONS": data.to_dict(orient="records")
        }
        existing_document = collection.find_one({"unique_id": unique_id})

        if existing_document:
            result = collection.update_one(
                {"unique_id": unique_id},
                {"$set": conference_publications_data}
            )
            print(f"Update result: {result.modified_count} document(s) updated.")
            if result.modified_count > 0:
                print(f"Conference publications data updated for {unique_id}.")
            else:
                print(f"No changes made for {unique_id}.")
        else:
            conference_publications_data["unique_id"] = unique_id
            collection.insert_one(conference_publications_data)
            print(f"Conference publications data added for {unique_id}.")
        
    except Exception as e:
        print(f"Error inserting conference publications data for {unique_id}: {e}")

def insert_book_publications(unique_id):
    folder_path = os.path.join(base_save_dir, unique_id)
    book_publications_file_path = os.path.join(folder_path, "BOOK-PUBLICATIONS.csv")

    if not os.path.exists(book_publications_file_path):
        print(f"Book publications file not found for {unique_id}. Skipping.")
        return

    try:
        data = pd.read_csv(book_publications_file_path)
        cleaned_columns = []
        for col in data.columns:
            cleaned_col = col.strip().replace(' ', '_')
            cleaned_columns.append(cleaned_col)
        data.columns = cleaned_columns

        book_publications_data = {
            "BOOK_PUBLICATIONS": data.to_dict(orient="records")
        }
        existing_document = collection.find_one({"unique_id": unique_id})

        if existing_document:
            result = collection.update_one(
                {"unique_id": unique_id},
                {"$set": book_publications_data}
            )
            print(f"Update result: {result.modified_count} document(s) updated.")
            if result.modified_count > 0:
                print(f"Book publications data updated for {unique_id}.")
            else:
                print(f"No changes made for {unique_id}.")
        else:
            book_publications_data["unique_id"] = unique_id
            collection.insert_one(book_publications_data)
            print(f"Book publications data added for {unique_id}.")
        
    except Exception as e:
        print(f"Error inserting book publications data for {unique_id}: {e}")

def insert_research_scholars(unique_id):
    folder_path = os.path.join(base_save_dir, unique_id)
    research_scholars_file_path = os.path.join(folder_path, "RESEARCH SCHOLARS.csv")

    if not os.path.exists(research_scholars_file_path):
        print(f"Research scholars file not found for {unique_id}. Skipping.")
        return

    try:
        data = pd.read_csv(research_scholars_file_path)
        cleaned_columns = []
        for col in data.columns:
            cleaned_col = col.strip().replace(' ', '_')
            cleaned_columns.append(cleaned_col)
        data.columns = cleaned_columns

        research_scholars_data = {
            "RESEARCH_SCHOLARS": data.to_dict(orient="records")
        }
        existing_document = collection.find_one({"unique_id": unique_id})

        if existing_document:
            result = collection.update_one(
                {"unique_id": unique_id},
                {"$set": research_scholars_data}
            )
            print(f"Update result: {result.modified_count} document(s) updated.")
            if result.modified_count > 0:
                print(f"Research scholars data updated for {unique_id}.")
            else:
                print(f"No changes made for {unique_id}.")
        else:
            research_scholars_data["unique_id"] = unique_id
            collection.insert_one(research_scholars_data)
            print(f"Research scholars data added for {unique_id}.")
        
    except Exception as e:
        print(f"Error inserting research scholars data for {unique_id}: {e}")

data = df.to_dict(orient="records")
try:
    collection.insert_many(data)
    print(f"Successfully inserted {len(data)} documents into the '{collection_name}' collection.")
except Exception as e:
    print(f"Error inserting initial data: {e}")

for _, row in df.iterrows():
    faculty_unique_id = row['unique_id']
    file_url = row.get('Upload Your Excel File Here', None)
    
    if not file_url:
        print(f"No file URL provided for {faculty_unique_id}. Skipping download.")
        continue
    
    print(f"Processing educational qualifications for {faculty_unique_id} with file URL: {file_url}")
    
    download_and_save_faculty_data(faculty_unique_id, file_url)
    
    insert_educational_qualifications_per_faculty(faculty_unique_id)
    insert_experience(faculty_unique_id)
    insert_conference_publications(faculty_unique_id)
    insert_book_publications(faculty_unique_id)
    insert_patents(faculty_unique_id)
    insert_projects(faculty_unique_id)
    insert_journal_publications(faculty_unique_id)
    insert_research_scholars(faculty_unique_id)

    print(f"Completed processing data for {faculty_unique_id}.")

def insert_department_data():
    collection = db["vision_and_mission"]
    with open("/root/Velammal-Engineering-College-Backend/docs/department_data.json", "r",encoding="utf-8") as file:
        documents = json.load(file)
        collection.insert_many(documents)

    print("Department documents inserted successfully.")

def insert_hod_datas():
    collection = db['HODS']
    with open("/root/Velammal-Engineering-College-Backend/docs/hods.json", "r",encoding="utf-8") as file:
        documents = json.load(file)
        collection.insert_many(documents)

    print("HOD documents inserted successfully.")

def insert_infrastructure_data():
    collection = db["infrastructure"]
    with open("/root/Velammal-Engineering-College-Backend/docs/infrastructure.json", "r",encoding="utf-8") as file:
        documents = json.load(file)
        collection.insert_many(documents)

    print("Infrastructure documents inserted successfully.")

def insert_student_activities_data():
    collection = db['student_activities'] 
    with open("/root/Velammal-Engineering-College-Backend/docs/student_activities.json", "r", encoding="utf-8") as file:
        documents = json.load(file)
        collection.insert_many(documents)
    
    print("Student documents inserted successfully.")

def insert_support_staff_data():
    collection = db['support_staffs'] 
    with open("/root/Velammal-Engineering-College-Backend/docs/support_staffs.json", "r",encoding="utf-8") as file:
        documents = json.load(file)
        collection.insert_many(documents)
    
    print("Support staffs documents inserted successfully.")

def insert_MOUs_data():
    collection = db['MOUs']
    folder_path = "/root/Velammal-Engineering-College-Backend/docs/MOUs/"
    for filename in os.listdir(folder_path):
        if filename.endswith(".json"):
            file_path = os.path.join(folder_path,filename)

            with open(file_path,"r") as file:
                documents = json.load(file)
                collection.insert_one(documents)
    
    print("All MOU documents have been inserted successfully.")

def insert_curriculum_data():
    collection = db['curriculum']
    with open("/root/Velammal-Engineering-College-Backend/docs/curriculum.json", "r",encoding="utf-8") as file:
        documents = json.load(file)
        collection.insert_many(documents)

    print("Cirrculum documents inserted successfully.")

def insert_events_data():
    collection = db['events']  
    with open("/root/Velammal-Engineering-College-Backend/docs/events.json", "r",encoding="utf-8") as file:
        documents = json.load(file)
        collection.insert_many(documents)

    print("Events documents inserted successfully.")

def insert_special_announcements():
    collection = db['special_announcement']  
    with open("/root/Velammal-Engineering-College-Backend/docs/special_announcements.json", "r",encoding="utf-8") as file:
        documents = json.load(file)
        collection.insert_many(documents)

    print("special_announcements documents inserted successfully.")

def insert_announcements_data():
   
    collection = db['announcements']  
    with open("/root/Velammal-Engineering-College-Backend/docs/announcements.json", "r",encoding="utf-8") as file:
        documents = json.load(file)
        collection.insert_many(documents)

    print("Announcements documents inserted successfully.")

def principal_data():
    collection = db["principal_data"]
    with open("/root/Velammal-Engineering-College-Backend/docs/principal_data.json", "r",encoding="utf-8") as file:
        documents = json.load(file)
        collection.insert_many(documents)

    print("Principals documents inserted successfully.")

def insert_admin_office_data():
    collection = db['admin_office']  
    with open("/root/Velammal-Engineering-College-Backend/docs/admin_office.json", "r",encoding="utf-8") as file:
        documents = json.load(file)
        collection.insert_many(documents)

    print("admin office documents inserted successfully.")

def insert_committee_data():

    collection = db['committee']  
    with open("/root/Velammal-Engineering-College-Backend/docs/committee.json", "r",encoding="utf-8") as file:
        documents = json.load(file)
        collection.insert_many(documents)

    print("Committee documents inserted successfully.")

def insert_regulation_data():
    collection = db['regulation']  
    with open("/root/Velammal-Engineering-College-Backend/docs/regulation.json", "r",encoding="utf-8") as file:
        documents = json.load(file)
        collection.insert_many(documents)

    print("regulation documents inserted successfully.")

def placement_team():
    collection = db["placement_team"]
    with open('/root/Velammal-Engineering-College-Backend/docs/placement_members.json', 'r',encoding="utf-8") as file:
        documents = json.load(file)
        collection.insert_many(documents)

    print(f"Placement Team Details Inserted")

def insert_intake_data():    
    collection = db["Intakes"]        
    with open('/root/Velammal-Engineering-College-Backend/docs/intakes.json', "r",encoding="utf-8") as file:
        documents = json.load(file)
    collection.insert_many(documents)

    print("Intake data inserted successfully.")

def insert_dean_and_associates_data():    
    collection = db["dean_and_associates"]        
    with open('/root/Velammal-Engineering-College-Backend/docs/dean_and_associates.json', "r",encoding="utf-8") as file:
        documents = json.load(file)
    collection.insert_many(documents)

    print("dean_and_associates data inserted successfully.")

def insert_placement_data():

    collection = db['placements_data']  
    with open("/root/Velammal-Engineering-College-Backend/docs/placements_data.json", "r",encoding="utf-8") as file:
        documents = json.load(file)
        collection.insert_many(documents)

    print("placement documents inserted successfully.")

def insert_curriculum_and_syllabus_data():

    collection = db['curriculum_and_syllabus']  
    with open("/root/Velammal-Engineering-College-Backend/docs/curriculum_and_syllabus.json", "r",encoding="utf-8") as file:
        documents = json.load(file)
        collection.insert_many(documents)

    print("curriculum_And_syllabus documents inserted successfully.")

def insert_banners():
    collection = db['banner']  
    with open("/root/Velammal-Engineering-College-Backend/docs/banner.json", "r",encoding="utf-8") as file:
        documents = json.load(file)
        collection.insert_many(documents)

    print("Banner documents inserted successfully.")

def insert_all_forms_data():

    collection = db['all_forms']  
    with open("/root/Velammal-Engineering-College-Backend/docs/all_forms.json", "r",encoding="utf-8") as file:
        documents = json.load(file)
        collection.insert_many(documents)

    print("all_forms documents inserted successfully.")

def insert_NBA_data():
    collection = db['nba']
    with open("/root/Velammal-Engineering-College-Backend/docs/nba.json", "r",encoding="utf-8") as file:
        documents = json.load(file)
        collection.insert_many(documents)

    print("NBA documents inserted successfully.")

def insert_naac_data():
    collection = db['naac']
    with open("/root/Velammal-Engineering-College-Backend/docs/naac.json", "r",encoding="utf-8") as file:
        documents = json.load(file)
        collection.insert_many(documents)
    print("NAAC documents inserted successfully.")

def insert_nirf_data():
    collection = db['nirf']
    with open("/root/Velammal-Engineering-College-Backend/docs/nirf.json", "r",encoding="utf-8") as file:
        documents = json.load(file)
        collection.insert_many(documents)
    print("NIRF documents inserted successfully.")

def insert_sidebar_details():
    collection= db['sidebar']
    with open ("/root/Velammal-Engineering-College-Backend/docs/sidebar.json","r",encoding="utf-8") as file:
        documents= json.load(file)
        collection.insert_many(documents)
    print("Sidebar documents inserted successfully")

def insert_iic_details():
    collection= db['iic']
    with open ("/root/Velammal-Engineering-College-Backend/docs/iic.json","r",encoding="utf-8") as file:
        documents= json.load(file)
        collection.insert_one(documents)
    print("iic documents inserted successfully")

def process_and_combine_Department_Activities_data_for_aids(folder_path, dept_id="001"):
    COLLECTION_NAME = "department_activities"
    collection = db[COLLECTION_NAME]
    
    def extract_data_from_docx(file_path):
        document = Document(file_path)
        activities = []
        
        for table in document.tables:
            for row in table.rows[1:]:  
                cells = row.cells
                if len(cells) >= 6:  
                    activity = {
                        "date": cells[1].text.strip(),
                        "name_of_event": cells[2].text.strip(),
                        "coordinator": cells[3].text.strip(),
                        "resource_person": cells[4].text.strip(),
                        "beneficiaries": cells[5].text.strip(),
                        "relevant_PO_PSO": cells[6].text.strip(),
                        "image_path": "image_path yet to be filled",
                    }
                    activities.append(activity)
        return activities

    combined_activities = []
    if not os.path.exists(folder_path) or not os.listdir(folder_path):
        print(f"Skipping '{folder_path}'. No data found for dept_id '{dept_id}'.")
        return

    for file_name in os.listdir(folder_path):
        if file_name.endswith(".docx"):
            file_path = os.path.join(folder_path, file_name)
            activities = extract_data_from_docx(file_path)
            combined_activities.extend(activities)

    if not combined_activities:
        print(f"No activity data extracted from '{folder_path}' for dept_id '{dept_id}'. Skipping.")
        return
    
    department_name=None
    
    for name, id in department_mapping1.items() :
        if id==dept_id:
            department_name = name

    combined_document = {
        "dept_id": dept_id,
        "department_name":department_name,
        "dept_activities": combined_activities
    }

    collection.update_one(
        {"dept_id": dept_id},
        {"$set": combined_document},
        upsert=True
    )
    print(f"Data combined and inserted into MongoDB under dept_id '{dept_id}'.")

aids_department_path = "/root/Velammal-Engineering-College-Backend/docs/AIDS-DEPT-ACT/"
process_and_combine_Department_Activities_data_for_aids(aids_department_path)

def insert_cscb_dept_activities_details():
    collection= db['department_activities']
    with open ("/root/Velammal-Engineering-College-Backend/docs/CSCBS-DEPT-ACT/006.json","r",encoding="utf-8") as file:
        documents= json.load(file)
        collection.insert_many(documents)
    print("cyber securtiy dept activities documents inserted successfully")

def insert_eie_dept_activities_details():
    collection= db['department_activities']
    with open ("/root/Velammal-Engineering-College-Backend/docs/EIE-DEPT-ACT/008.json","r",encoding="utf-8") as file:
        documents= json.load(file)
        collection.insert_many(documents)
    print("EIE dept activities documents inserted successfully")

def insert_mech_dept_activities_details():
    collection= db['department_activities']
    with open ("/root/Velammal-Engineering-College-Backend/docs/MECH-DEPT-ACT/013.json","r",encoding="utf-8") as file:
        documents= json.load(file)
        collection.insert_many(documents)
    print("MECH dept activities documents inserted successfully")

def insert_math_dept_activities_details():
    collection= db['department_activities']
    with open ("/root/Velammal-Engineering-College-Backend/docs/MATH-DEPT-ACT/012.json","r",encoding="utf-8") as file:
        documents= json.load(file)
        collection.insert_many(documents)
    print("MATH dept activities documents inserted successfully")

def insert_eee_dept_activities_details():
    collection= db['department_activities']
    with open ("/root/Velammal-Engineering-College-Backend/docs/EEE-DEPT-ACT/007.json","r",encoding="utf-8") as file:
        documents= json.load(file)
        collection.insert_many(documents)
    print("EEE dept activities documents inserted successfully")

def insert_civil_dept_activities_details():
    collection= db['department_activities']
    with open ("/root/Velammal-Engineering-College-Backend/docs/CIVIL-DEPT-ACT/004.json","r",encoding="utf-8") as file:
        documents= json.load(file)
        collection.insert_many(documents)
    print("civil dept activities documents inserted successfully")

def insert_auto_dept_activities_details():
    collection= db['department_activities']
    with open ("/root/Velammal-Engineering-College-Backend/docs/AUTO-DEPT-ACT/002.json","r",encoding="utf-8") as file:
        documents= json.load(file)
        collection.insert_many(documents)
    print("auto dept activities documents inserted successfully")

def insert_alumni_data(directory_path='/root/Velammal-Engineering-College-Backend/docs/ALUMINI'):
    collection = db["alumni"]

    for filename in os.listdir(directory_path):
        if filename.endswith(".json"):
            file_path = os.path.join(directory_path, filename)
            with open(file_path, "r") as file:
                data = json.load(file)
                if isinstance(data, list):
                    collection.insert_many(data)
                elif isinstance(data, dict):
                    collection.insert_one(data)
                else:
                    print(f"Unsupported data format in file: {filename}")

    print("Data from JSON files has been inserted into the 'alumni' collection.")

insert_department_data()
insert_hod_datas()
insert_infrastructure_data()
insert_student_activities_data()
insert_support_staff_data()
insert_MOUs_data()
insert_curriculum_data()
insert_events_data()
insert_announcements_data()
insert_special_announcements()
principal_data()
insert_admin_office_data()
placement_team()
insert_regulation_data()
insert_intake_data()
insert_committee_data()
insert_placement_data()
insert_dean_and_associates_data()
insert_curriculum_and_syllabus_data()
insert_all_forms_data()
insert_alumni_data()
insert_banners()
insert_NBA_data()
insert_naac_data()
insert_nirf_data()
insert_sidebar_details()
insert_iic_details()
insert_cscb_dept_activities_details()
insert_eie_dept_activities_details()
insert_mech_dept_activities_details()
insert_math_dept_activities_details()
insert_eee_dept_activities_details()
insert_civil_dept_activities_details()
insert_auto_dept_activities_details()

department_mapping = {
    "Artificial Intelligence and Data Science": "001",
    "Automobile Engineering": "002",
    "Chemistry": "003",
    "Civil Engineering": "004",
    "Computer Science & Engineering": "005",
    "Computer Science and Engineering (CYBER SECURITY)": "006",
    "Electrical & Electronics Engineering": "007",
    "Electronics & Instrumentation Engineering": "008",
    "Electronics and Communication Engineering": "009",
    "English": "010",
    "Information Technology": "011",
    "Mathematics": "012",
    "Mechancial Engineering": "013",
    "Tamil": "014",
    "Physics": "015"
}

def insert_incubation_data():
    collection= db['incubation']
    with open ("/root/Velammal-Engineering-College-Backend/docs/incubation.json","r",encoding="utf-8") as file:
        documents= json.load(file)
        collection.insert_many(documents)
    print("Incubation documents inserted successfully")
    
def insert_army_data():
    collection = db['army']
    with open("/root/Velammal-Engineering-College-Backend/docs/ncc_army.json", "r",encoding="utf-8") as file:
        documents = json.load(file)
        collection.insert_many(documents)
    print("armydocuments inserted successfully.")

def insert_navy_data():
    collection = db['navy']
    with open("/root/Velammal-Engineering-College-Backend/docs/navy.json", "r",encoding="utf-8") as file:
        documents = json.load(file)
        collection.insert_many(documents)
    print("navy documents inserted successfully.")

def insert_faculty_data(folder_path):
    department_name=None
    with open(r"/root/Velammal-Engineering-College-Backend/docs/prev_faculty.json","r",encoding="utf-8") as file:
        data=json.load(file)
    try:
        collection = db['faculty_data']
        if not os.path.exists(folder_path):
            print(f"Error: Folder path '{folder_path}' does not exist.")
            return

        for file_name in os.listdir(folder_path):
            
            if file_name.endswith(".xlsx"):
                file_path = os.path.join(folder_path, file_name)

                dept_id = os.path.splitext(file_name)[0]

                try:
                    df = pd.read_excel(file_path)
                except Exception as e:
                    print(f"Error reading Excel file '{file_name}': {e}")
                    continue
                required_columns = [
                    "Name", "Designation", "Photo", "Google Scholar Profile",
                    "Research Gate", "Orchid Profile", "Publon Profile",
                    "Scopus Author Profile", "LinkedIn Profile", "unique_id"
                ]
                missing_columns = [col for col in required_columns if col not in df.columns]
                if missing_columns:
                    print(f"Error: Missing columns in '{file_name}': {missing_columns}")
                    continue 

                faculty_list = []
                for index, row in df.iterrows():
                    try:
                        faculty_data = {
                            "name": row["Name"],
                            "designation": row["Designation"],
                            "photo": row["Photo"],
                            "profiles": {
                                "google_scholar": row["Google Scholar Profile"],
                                "research_gate": row["Research Gate"],
                                "orchid": row["Orchid Profile"],
                                "publon": row["Publon Profile"],
                                "scopus": row["Scopus Author Profile"],
                                "linkedin": row["LinkedIn Profile"]
                            },
                            "unique_id": row["unique_id"]
                        }
                        faculty_list.append(faculty_data)
                    except Exception as e:
                        print(f"Error processing row {index} in '{file_name}': {e}")
                for name, id in department_mapping1.items() :
                    if id==dept_id:
                        department_name=name
                        
                        department_document = {
                            "department_name": department_name,
                            "dept_id": dept_id,
                            "previous_faculty_pdf_path":data.get(dept_id),
                            "faculty_members": faculty_list
                        }
                if faculty_list:
                    try:
                        collection.insert_one(department_document)
                    except Exception as e:
                        print(f"Error inserting document for '{dept_id}' into MongoDB: {e}")
                else:
                    print(f"No valid faculty data to insert for '{file_name}'.")
    except Exception as e:
        print(f"Unexpected error: {e}")

    print("Faculty Data Insertion Done")
    return

insert_faculty_data(folder_path=r"/root/Velammal-Engineering-College-Backend/docs/STAFF-DATA/")

# SPORTS DATA INSERTIONS

def insert_sports_Zonal_results():
    collection = db["sports_data"]
    with open("/root/Velammal-Engineering-College-Backend/docs/sports_zonal.json", "r",encoding="utf-8") as file:
        documents = json.load(file)
        collection.insert_many(documents)

    print("Sports Zonal data inserted successfully.")

def insert_sports_Zonal_images():
    collection = db["sports_data"]
    with open("/root/Velammal-Engineering-College-Backend/docs/zonal_images.json", "r",encoding="utf-8") as file:
        documents = json.load(file)
        collection.insert_many(documents)

    print("Sports Zonal images data inserted successfully.")

def insert_sports_faculty_data():
    collection = db["sports_data"]
    with open("/root/Velammal-Engineering-College-Backend/docs/sports_faculty.json", "r",encoding="utf-8") as file:
        documents = json.load(file)
        collection.insert_one(documents)

    print("sports faculty data inserted successfully.")

def insert_sports_achievements_data():
    collection = db["sports_data"]
    with open("/root/Velammal-Engineering-College-Backend/docs/sports_achievements.json", "r",encoding="utf-8") as file:
        documents = json.load(file)
        collection.insert_one(documents)

    print("sports achievements data inserted successfully.")

def insert_sports_coordinates():
    collection = db["sports_data"]
    with open("/root/Velammal-Engineering-College-Backend/docs/sports_coordinates.json", "r",encoding="utf-8") as file:
        documents = json.load(file)
        collection.insert_many(documents)

    print("sports coordinates data inserted successfully.")

def insert_other_facilties():
    collection = db["other_facilties"]
    with open("/root/Velammal-Engineering-College-Backend/docs/other_facilties.json", "r",encoding="utf-8") as file:
        documents = json.load(file)
        collection.insert_many(documents)

    print("Other Facilties data inserted successfully.")

def insert_library_data():
    collection = db["library"]
    with open("/root/Velammal-Engineering-College-Backend/docs/library.json", "r",encoding="utf-8") as file:
        documents = json.load(file)
        collection.insert_many(documents)

    print("Library data inserted successfully.")

def insert_nss_personnel():
    collection = db["nss_data"]
    with open("/root/Velammal-Engineering-College-Backend/docs/nss_personnel.json", "r",encoding="utf-8") as file:
        documents = json.load(file)
        collection.insert_many(documents)

    print("nss_personnel data inserted successfully.")

def insert_nss_carousal():
    collection = db["nss_data"]
    with open("/root/Velammal-Engineering-College-Backend/docs/nss_carousal.json", "r",encoding="utf-8") as file:
        documents = json.load(file)
        collection.insert_many(documents)
    
    print("nss_carousal data inserted successfully.")

def insert_yrc_data():
    collection = db["yrc_data"]
    with open("/root/Velammal-Engineering-College-Backend/docs/yrc_carousal.json", "r",encoding="utf-8") as file:
        documents = json.load(file)
        collection.insert_many(documents)

    print("yrc_carousal data inserted successfully.")

    with open("/root/Velammal-Engineering-College-Backend/docs/yrc_personnel.json", "r",encoding="utf-8") as file:
        documents = json.load(file)
        collection.insert_many(documents)
    print("yrc_personnel data inserted successfully.")

def insert_overall_department_research():
    collection = db['overall_research']
    with open("/root/Velammal-Engineering-College-Backend/docs/research_data.json","r",encoding="utf-8") as file:
        documents = json.load(file)
        collection.insert_one(documents)
    
    print("inserted overall research data")

def insert_department_research_data():
    collection = db['department_research_data']
    
    folder_path = "/root/Velammal-Engineering-College-Backend/docs/new_research_data"
    
    for file_name in os.listdir(folder_path):
        if file_name.endswith(".json"):
            file_path = os.path.join(folder_path, file_name)
            
            try:
                with open(file_path, "r") as file:
                    document = json.load(file)
                    collection.insert_one(document)
            except Exception as e:
                print(f"Error inserting {file_name}: {e}")
    
    print("All available Department Research documents inserted successfully.")

def insert_warden_hostel_data():
    collection = db['warden_profile']
    with open("/root/Velammal-Engineering-College-Backend/docs/warden_profile.json","r",encoding="utf-8") as file:
        documents = json.load(file)
        collection.insert_many(documents)
    
    print("inserted warden profile data")

insert_sports_Zonal_results()
insert_sports_Zonal_images()
insert_sports_faculty_data()
insert_sports_achievements_data()
insert_other_facilties()
insert_library_data()
insert_sports_coordinates()
insert_nss_personnel()
insert_nss_carousal()
insert_yrc_data()
insert_overall_department_research()
insert_department_research_data()
insert_warden_hostel_data()
insert_incubation_data()
insert_army_data()
insert_navy_data()

def add_hostel_student_database():
    collection = db["student_database"]
    storage_dir = r"/root/Velammal-Engineering-College-Backend/docs"
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

#add_hostel_student_database()

department_mapping1 = {
    "001": "Artificial Intelligence and Data Science (AI&DS)",
    "002": "Automobile Engineering (AUTO)",
    "003": "Chemistry",
    "004": "Civil Engineering (CIVIL)",
    "005": "Computer Science & Engineering (CSE)",
    "006": "Computer Science and Engineering (CYBER SECURITY)",
    "007": "Electrical & Electronics Engineering (EEE)",
    "008": "Electronics & Instrumentation Engineering (EIE)",
    "009": "Electronics and Communication Engineering (ECE)",
    "010": "English",
    "011": "Information Technology (IT)",
    "012": "Mathematics",
    "013": "Mechancial Engineering (MECH)",
    "014": "Tamil",
    "015": "Physics"
}

parent_folder = "/root/Velammal-Engineering-College-Backend/docs/depts_fol"

def convert_df_to_json(df):
    df = df.astype(str)
    return {col: df[col].dropna().tolist() for col in df.columns}

def format_sheet_name(sheet_name):
    return sheet_name.lower().replace(" ", "_")

def extract_year_from_filename(filename):
    match = re.search(r"(\d{4}-\d{2})", filename)
    return match.group(1) if match else "Unknown"

for department_id in os.listdir(parent_folder):
    department_path = os.path.join(parent_folder, department_id)
    
    if not os.path.isdir(department_path) or department_id not in department_mapping1:
        continue

    department_name = department_mapping1[department_id]
    
    research_data = []

    for file in os.listdir(department_path):
        if file.endswith(".xlsx") or file.endswith(".xls"):
            file_path = os.path.join(department_path, file)
            
            year = extract_year_from_filename(file)
            xls = pd.ExcelFile(file_path)
            
            data_dict = {}

            for sheet_name in xls.sheet_names:
                formatted_sheet_name = format_sheet_name(sheet_name)
                df = pd.read_excel(xls, sheet_name=sheet_name)
                data_dict[formatted_sheet_name] = convert_df_to_json(df)

            research_data.append({
                "year": year,
                "data": data_dict
            })

    output_json = {
        "department_id": department_id,
        "department_name": department_name,
        "research_data": research_data
    }
    output_file = os.path.join(parent_folder, f"{department_id}.json")
    with open(output_file, "w", encoding="utf-8") as json_file:
        json.dump(output_json, json_file, indent=4)

    print(f"✅ Processed {department_name} ({department_id}) → {output_file}")

print("🎉 All department files processed successfully!")

#OLD RESEARCH ENDPOINTS DATA INSERTIONS

'''def upload_research_data(folder_path):
    collection = db['research_data']
    for filename in os.listdir(folder_path):
        if filename.endswith('.json'):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'r') as file:
                try:
                    data = json.load(file)
                    dept_id = filename.split('.')[0]
                    if dept_id not in department_mapping.values():
                        print(f"Skipping unrecognized dept_id: {dept_id}")
                        continue

                    collection.insert_one({"dept_id": dept_id, "data": data})
                    print(f"✅ Successfully inserted data for {dept_id}")

                except json.JSONDecodeError as e:
                    print(f"❌ Error decoding JSON from {filename}: {e}")
                except Exception as e:
                    print(f"❌ Error processing {filename}: {e}")

folder_path = r'/root/Velammal-Engineering-College-Backend/docs/RESEARCH-DATA'
upload_research_data(folder_path)'''


#OLD NSS ENDPOINTS DATA INSERTIONS

'''def insert_nss_podcast():
    collection= db['nsspodcast']
    with open ("/root/Velammal-Engineering-College-Backend/docs/nsspodcast.json","r") as file:
        documents= json.load(file)
        collection.insert_many(documents)
    print("NSS_Podcast documents inserted successfully")

def insert_nss_home_data():
    collection = db["nsshome"]
    with open("/root/Velammal-Engineering-College-Backend/docs/nss_home.json", "r") as file:
        documents = json.load(file)
        collection.insert_one(documents)

    print("NSS home data inserted successfully.")

def insert_nss_events():
    collection = db["nssgallery"]
    with open("/root/Velammal-Engineering-College-Backend/docs/nss_gallery.json", "r") as file:
        documents = json.load(file)
        collection.insert_many(documents)

    print("NSS gallery data inserted successfully.")

def insert_nss_faculty_data():
    collection = db["nss_faculty"]
    with open("/root/Velammal-Engineering-College-Backend/docs/nss_faculty.json", "r") as file:
        documents = json.load(file)
        collection.insert_one(documents)

    print("NSS faculty data inserted successfully.")

insert_nss_podcast()
insert_nss_home_data()
insert_nss_events()
insert_nss_faculty_data()'''