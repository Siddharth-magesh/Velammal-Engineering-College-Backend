import os
import requests
import pandas as pd
from pymongo import MongoClient
from docx import Document
import json

mongo_uri = "mongodb://localhost:27017/"
db_name = "VEC"
collection_name = "staff_details"

file_path = r"/Velammal-Engineering-College-Backend/docs/VEC Faculty Details.csv"
photo_base_dir = r"/Velammal-Engineering-College-Backend/database/static/profile_photos/"
base_save_dir = r"/Velammal-Engineering-College-Backend/database/static/staff_scholar_details/"

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
    "Physical Education": "014",
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


df = df.head(1)
df['unique_id'] = [
    generate_unique_id(i, df.at[i, 'Department Name'], df.at[i, 'Designation'])
    for i in range(len(df))
]


def download_image(unique_id, photo_url):
    if not photo_url or not isinstance(photo_url, str):
        return None
    file_name = f"{unique_id}.jpg"
    save_dir = os.path.join(photo_base_dir, unique_id)
    os.makedirs(save_dir, exist_ok=True)
    file_path = os.path.join(save_dir, file_name)
    try:
        if "drive.google.com" in photo_url:
            file_id = photo_url.split("id=")[-1]
            photo_url = f"https://drive.google.com/uc?id={file_id}"
        response = requests.get(photo_url, stream=True)
        if response.status_code == 200:
            with open(file_path, "wb") as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
            return file_path
        else:
            print(f"Failed to download image for {unique_id}. URL: {photo_url}")
            return None
    except Exception as e:
        print(f"Error downloading image for {unique_id}: {e}")
        return None

df['Photo'] = df.apply(lambda row: download_image(row['unique_id'], row['Photo']), axis=1)

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
    with open("/Velammal-Engineering-College-Backend/docs/department_data.json", "r") as file:
        documents = json.load(file)
        collection.insert_many(documents)

    print("Department documents inserted successfully.")

def insert_hod_datas():
    collection = db['HODS']
    with open("/Velammal-Engineering-College-Backend/docs/hods.json", "r") as file:
        documents = json.load(file)
        collection.insert_many(documents)

    print("HOD documents inserted successfully.")

def insert_infrastructure_data():
    collection = db["infrastructure"]
    with open("/Velammal-Engineering-College-Backend/docs/infrastructure.json", "r") as file:
        documents = json.load(file)
        collection.insert_many(documents)

    print("Infrastructure documents inserted successfully.")

def insert_student_activities_data():
    collection = db['student_activities'] 
    with open("/Velammal-Engineering-College-Backend/docs/student_activities.json", "r") as file:
        documents = json.load(file)
        collection.insert_many(documents)
    
    print("Student documents inserted successfully.")

def insert_support_staff_data():
    collection = db['support_staffs'] 
    with open("/Velammal-Engineering-College-Backend/docs/support_staffs.json", "r") as file:
        documents = json.load(file)
        collection.insert_many(documents)
    
    print("Support staffs documents inserted successfully.")

def insert_MOUs_data():
    collection = db['MOUs'] 
    with open("/Velammal-Engineering-College-Backend/docs/MOUs.json", "r") as file:
        documents = json.load(file)
        collection.insert_many(documents)
    
    print("MOUs documents inserted successfully.")

def insert_curriculum_data():
    collection = db['curriculum']  
    with open("/Velammal-Engineering-College-Backend/docs/curriculum.json", "r") as file:
        documents = json.load(file)
        collection.insert_many(documents)

    print("Cirrculum documents inserted successfully.")

def process_and_combine_Department_Activities_data(folder_path, dept_id):
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

    combined_document = {
        "dept_id": dept_id,
        "dept_activities": combined_activities
    }

    collection.update_one(
        {"dept_id": dept_id},
        {"$set": combined_document},
        upsert=True
    )
    print(f"Data combined and inserted into MongoDB under dept_id '{dept_id}'.")

insert_department_data()
insert_hod_datas()
insert_infrastructure_data()
insert_student_activities_data()
insert_support_staff_data()
insert_MOUs_data()
insert_curriculum_data()

department_paths = {
    "1": "/Velammal-Engineering-College-Backend/docs/AIDS-DEPT-ACT/",
    "2": "/Velammal-Engineering-College-Backend/docs/CSE-DEPT-ACT/",
    "3": "/Velammal-Engineering-College-Backend/docs/ECE-DEPT-ACT/",
    "4": "/Velammal-Engineering-College-Backend/docs/EEE-DEPT-ACT/",
    "5": "/Velammal-Engineering-College-Backend/docs/MECH-DEPT-ACT/",
    "6": "/Velammal-Engineering-College-Backend/docs/CIVIL-DEPT-ACT/",
    "7": "/Velammal-Engineering-College-Backend/docs/IT-DEPT-ACT/",
    "8": "/Velammal-Engineering-College-Backend/docs/BME-DEPT-ACT/",
    "9": "/Velammal-Engineering-College-Backend/docs/EIE-DEPT-ACT/",
    "10": "/Velammal-Engineering-College-Backend/docs/MBA-DEPT-ACT/",
    "11": "/Velammal-Engineering-College-Backend/docs/MCA-DEPT-ACT/",
    "12": "/Velammal-Engineering-College-Backend/docs/AUTO-DEPT-ACT/",
    "13": "/Velammal-Engineering-College-Backend/docs/MTECH-IT-DEPT-ACT/",
    "14": "/Velammal-Engineering-College-Backend/docs/ARCH-DEPT-ACT/",
    "15": "/Velammal-Engineering-College-Backend/docs/SCI-HUM-DEPT-ACT/",
}

for dept_id, path in department_paths.items():
    process_and_combine_Department_Activities_data(path, dept_id)

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
    "Physical Education": "014",
    "Physics": "015"
}

def upload_research_data(folder_path):
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

folder_path = r'D:\Velammal-Engineering-College-Backend\docs\RESEARCH-DATA'
upload_research_data(folder_path)