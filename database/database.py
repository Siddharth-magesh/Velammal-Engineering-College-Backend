import os
import requests
import pandas as pd
from pymongo import MongoClient

mongo_uri = "mongodb://localhost:27017/"
db_name = "VEC"
collection_name = "staff_details"

file_path = r"D:\vec_backend\VEC Faculty Details.csv"
photo_base_dir = r"static/profile_photos/"
base_save_dir = r"D:\vec_backend\staff_scholar_details"

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


df = df.head(10)
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