import os
import pymongo
import pandas as pd

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["VEC"]
collection = db["Staff_details"]

folder_path = r"/Velammal-Engineering-College-Backend/docs/STAFF-DATA/"

def insert_faculty_data(folder_path):
    try:
        if not os.path.exists(folder_path):
            print(f"Error: Folder path '{folder_path}' does not exist.")
            return

        for file_name in os.listdir(folder_path):
            if file_name.endswith(".xlsx"):
                file_path = os.path.join(folder_path, file_name)
                print(f"Processing file: {file_path}")

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
                
                department_document = {
                    "dept_id": dept_id,
                    "faculty_members": faculty_list
                }
                if faculty_list:
                    try:
                        collection.insert_one(department_document)
                        print(f"Inserted document for department '{dept_id}' successfully.")
                    except Exception as e:
                        print(f"Error inserting document for '{dept_id}' into MongoDB: {e}")
                else:
                    print(f"No valid faculty data to insert for '{file_name}'.")
    except Exception as e:
        print(f"Unexpected error: {e}")

    print("Data insertion process completed.")
    return

insert_faculty_data(folder_path)
