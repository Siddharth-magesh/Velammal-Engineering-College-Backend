from pymongo import MongoClient
from docx import Document
import os

MONGO_URI = "mongodb://localhost:27017/" 
DATABASE_NAME = "VEC"


def process_and_combine_data(folder_path, dept_id):

    COLLECTION_NAME = "department_activities"

    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
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
    for file_name in os.listdir(folder_path):
        if file_name.endswith(".docx"):
            file_path = os.path.join(folder_path, file_name)
            activities = extract_data_from_docx(file_path)
            combined_activities.extend(activities)

    combined_document = {
        "dept_id": dept_id,
        "dept_activities": combined_activities
    }

    collection.update_one(
        {"dept_id": dept_id},
        {"$set": combined_document},
        upsert=True
    )
    print(f"All data combined and inserted into MongoDB under dept_id '{dept_id}'.")



#create separate folder path for each departments with department_activities
'''"Artificial Intelligence and Data Science": "001",
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
'''
department_paths = {
    "1": "P:\\dataset\\college_website",
    "2": "P:\\dataset\\college_website",
    "3": "P:\\dataset\\college_website",
    "4": "P:\\dataset\\college_website",
    "5": "P:\\dataset\\college_website",
    "6": "P:\\dataset\\college_website",
    "7": "P:\\dataset\\college_website",
    "8": "P:\\dataset\\college_website",
    "9": "P:\\dataset\\college_website",
    "10": "P:\\dataset\\college_website",
    "11": "P:\\dataset\\college_website",
    "12": "P:\\dataset\\college_website",
    "13": "P:\\dataset\\college_website",
    "14": "P:\\dataset\\college_website",
    "15": "P:\\dataset\\college_website",
}

for dept_id, path in department_paths.items():
    process_and_combine_data(path, dept_id)