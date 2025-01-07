import os
import requests
import pandas as pd
from pymongo import MongoClient

mongo_uri = "mongodb://localhost:27017/"
db_name = "VEC"
collection_name = "staff_details"

file_path = r"docs/VEC Faculty Details.csv"
photo_base_dir = r"database/static/profile_photos/"
base_save_dir = r"database/static/staff_scholar_details/"

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


df = df.head(5)
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

    departments = [
        {
            "department_id": 1,
            "department_name": "Artificial Intelligence and Data Science",
            "department_image": "url_to_ai_ds_image",
            "department_quotes": "Empowering innovation through data-driven intelligence.",
            "vision": "To achieve value based education and bring idealistic, ethical engineers to meet the thriving trends and technology in the field of Artificial Intelligence and Data Science",
            "mission": [
                "To engage students with the core competence to solve real world problems using Artificial Intelligence.",
                "To enlighten students into technically proficient engineers through innovation in Data Science.",
                "To involve students with industry collaboration, career guidance and leadership skills.",
                "To mould students as ethical professionals to bring morals to individual and society."
            ],
            "about_department": "Department of Artificial Intelligence aims to produce computing graduates with high potency, apply, design and develop systems to pertain and to integrate both software and hardware devices, utilize modern approaches in programming and problem solving techniques. The Department was established in the year 2020 with the main objective of providing quality education in the field of Engineering and Technology. It is recognized as nodal center under Anna University. The Department has proved to be a center of excellence in Academic, Sponsored research and Continuing Education Programme."
        },
        {
            "department_id": 2,
            "department_name": "Automobile Engineering",
            "department_image": "url_to_cse_image",
            "department_quotes": "Innovating the future of technology.",
            "vision": "To excel in computer science education, research, and innovation.",
            "mission": [
                "Deliver quality education in computer science engineering.",
                "Foster research in emerging fields of technology.",
                "Build industry-ready professionals with strong ethical values."
            ],
            "about_department": "The department emphasizes core computing skills and modern engineering practices."
        },
        {
            "department_id": 3,
            "department_name": "Chemistry ",
            "department_image": "url_to_it_image",
            "department_quotes": "Transforming information into solutions.",
            "vision": "To be a leader in IT education and innovation, bridging technology and business.",
            "mission": [
                "Impart theoretical and practical knowledge in IT.",
                "Promote research in information systems and technologies.",
                "Encourage entrepreneurship and innovation."
            ],
            "about_department": "The department bridges the gap between technology and practical implementation."
        },
        {
            "department_id": 4,
            "department_name": "Civil Engineering",
            "department_image": "url_to_cybersecurity_image",
            "department_quotes": "Securing the digital world.",
            "vision": "To be a leader in cybersecurity education and research, ensuring a safer digital environment.",
            "mission": [
                "Provide a comprehensive understanding of cybersecurity concepts.",
                "Conduct research in emerging threats and solutions.",
                "Train professionals to safeguard information and systems."
            ],
            "about_department": "The department focuses on equipping students with skills to tackle modern cybersecurity challenges."
        },
        {
            "department_id": 5,
            "department_name": "Computer Science & Engineering   ",
            "department_image": "url_to_ece_image",
            "department_quotes": "Connecting the world through innovation.",
            "vision": "To pioneer in electronics and communication engineering education and research.",
            "mission": [
                "Develop expertise in electronics and communication technologies.",
                "Promote innovative research for societal benefits.",
                "Prepare students for leadership roles in industry and academia."
            ],
            "about_department": "The department specializes in modern communication systems and electronic design."
        },
        {
            "department_id": 6,
            "department_name": "Computer Science and Engineering (CYBER SECURITY)   ",
            "department_image": "url_to_eee_image",
            "department_quotes": "Powering the future.",
            "vision": "To excel in electrical and electronics engineering education and sustainable innovation.",
            "mission": [
                "Provide a strong foundation in electrical and electronics engineering.",
                "Encourage research in renewable energy and smart systems.",
                "Equip students with problem-solving skills for the energy sector."
            ],
            "about_department": "The department addresses challenges in energy systems and electrical technologies."
        },
        {
            "department_id": 7,
            "department_name": "Electrical & Electronics Engineering   ",
            "department_image": "url_to_eie_image",
            "department_quotes": "Precision engineering for a better world.",
            "vision": "To lead in electronic and instrumentation engineering education and innovation.",
            "mission": [
                "Focus on quality education in instrumentation and control systems.",
                "Promote research in automation and intelligent systems.",
                "Prepare students for industrial and academic excellence."
            ],
            "about_department": "The department emphasizes control systems and precision technologies."
        },
        {
            "department_id": 8,
            "department_name": "Electronics & Instrumentation Engineering ",
            "department_image": "url_to_civil_image",
            "department_quotes": "Building the foundation for tomorrow.",
            "vision": "To be a leader in civil engineering education, research, and sustainable development.",
            "mission": [
                "Provide in-depth knowledge of civil engineering principles.",
                "Encourage innovation in construction and design.",
                "Promote sustainable and eco-friendly engineering practices."
            ],
            "about_department": "The department focuses on modern construction technologies and sustainability."
        },
        {
            "department_id": 9,
            "department_name": "Electronics and Communication Engineering ",
            "department_image": "url_to_mechanical_image",
            "department_quotes": "Engineering the tools of the future.",
            "vision": "To achieve excellence in mechanical engineering education and research.",
            "mission": [
                "Deliver comprehensive knowledge of mechanical systems.",
                "Promote research in advanced manufacturing and materials.",
                "Prepare students for global challenges in engineering."
            ],
            "about_department": "The department emphasizes mechanical system design and innovation."
        },
        {
            "department_id": 10,
            "department_name": "English ",
            "department_image": "url_to_automobile_image",
            "department_quotes": "Driving innovation forward.",
            "vision": "To be a center of excellence in automobile engineering education and innovation.",
            "mission": [
                "Provide expertise in automotive technologies.",
                "Encourage research in sustainable and electric vehicles.",
                "Prepare industry-ready professionals for the automotive sector."
            ],
            "about_department": "The department focuses on automotive design and sustainable transportation."
        },
        {
            "department_id": 11,
            "department_name": "Information Technology",
            "department_image": "url_to_english_image",
            "department_quotes": "Communicating the world with clarity and creativity.",
            "vision": "To enhance linguistic and literary skills for global communication and cultural understanding.",
            "mission": [
                "Promote excellence in English language and literature.",
                "Foster critical thinking and creativity through language.",
                "Prepare students for effective communication in diverse contexts."
            ],
            "about_department": "The department focuses on linguistic proficiency and literary appreciation."
        },
        {
            "department_id": 12,
            "department_name": "Mathematics",
            "department_image": "url_to_chemistry_image",
            "department_quotes": "Exploring the building blocks of matter.",
            "vision": "To excel in chemical education and research for sustainable development.",
            "mission": [
                "Provide in-depth knowledge of chemical principles.",
                "Encourage research in green and sustainable chemistry.",
                "Prepare students for careers in chemical industries and research."
            ],
            "about_department": "The department emphasizes chemical analysis and sustainable practices."
        },
        {
            "department_id": 13,
            "department_name": "Mechancial Engineering",
            "department_image": "url_to_mathematics_image",
            "department_quotes": "Unlocking the power of numbers and logic.",
            "vision": "To be a leader in mathematical education and research, fostering analytical and problem-solving skills.",
            "mission": [
                "Provide a strong foundation in mathematical concepts.",
                "Encourage interdisciplinary research involving mathematics.",
                "Equip students with analytical skills for diverse applications."
            ],
            "about_department": "The department focuses on pure and applied mathematical sciences."
        },
        {
            "department_id": 14,
            "department_name": "Physical Education",
            "department_image": "url_to_physics_image",
            "department_quotes": "Unveiling the mysteries of the universe.",
            "vision": "To excel in physics education and research, inspiring scientific curiosity.",
            "mission": [
                "Provide a strong foundation in fundamental and applied physics.",
                "Encourage research in emerging areas of physical sciences.",
                "Prepare students for careers in academia, industry, and research."
            ],
            "about_department": "The department emphasizes understanding and applying the principles of physics."
        },
        {
            "department_id": 15,
            "department_name": "Physics",
            "department_image": "url_to_biotech_image",
            "department_quotes": "Harnessing life sciences for a better tomorrow.",
            "vision": "To lead in biotechnology education and research for sustainable development.",
            "mission": [
                "Provide comprehensive knowledge in biotechnology.",
                "Encourage research in genetic engineering and bioprocess technology.",
                "Prepare students for global challenges in biotechnology and healthcare."
            ],
            "about_department": "The department focuses on cutting-edge research in life sciences and biotechnology applications."
        }
    ]

    collection.insert_many(departments)
    print("Department documents inserted successfully.")

def insert_hod_datas():
    hod_collection = db['HODS']

    departments = [
        {
            "Name": "Dr. VISU",
            "Unique_id": "VEC-001-01-77",
            "Qualification": ["M.E","PhD"],
            "Hod_message": "Welcome to the Artificial Intelligence Department!",
            "Image": "vec pics/Dr.P.VISU - Dr. P. Visu Prof & Head - Dept.of AI & DS.jpg",  # Path to the image
        
            "Social_media_links": {
                "LinkedIn": "https://www.linkedin.com/in/dr-visu-p-12a78961/?trk=public_profile_browsemap&originalSubdomain=in",
                "Google Scholar": "https://scholar.google.co.in/citations?view_op=list_works&hl=en&authuser=2&hl=en&user=KfwgAmoAAAAJ&sortby=pubdate&authuser=2",
                "Research Gate": "https://www.researchgate.net/profile/Pandu-Visu",
                "Orchid Profile": "https://orcid.org/my-orcid?orcid=0000-0001-8020-1678",
                "Publon": "https://www.webofscience.com/wos/author/record/21718142",
                "Scopus": "https://www.scopus.com/results/results.uri?src=s&sort=plf-f&st1=VISU&st2=P&nlo=1&nlr=20&nls=count-f&sid=de56d96861725e0547809c9ac4a37743&sot=anl&sdt=aut&sl=29&s=AU-ID%28%22Visu%2c+P.%22+35744043700%29&cl=t&offset=1&ss=plf-f&ws=r-f&ps=plf-f&cs=r-f&origin=resultslist&zone=queryBar"
            }
        },
        {
        
            "Name": "Dr. MARY JOANS",
            "Unique_id": "VEC-009-01-90",
            "Qualification":  ["M.E","PhD"],
            "Hod_message": "Welcome to the Electronics and Communication Engineering Department!",
            "Image": "vec pics/DR.S.MARY_JOANS_PHOTO_22-23_optimized_50 - Dr. S. Mary Joans Professor & Head.jpg",  # Path to the image
        
            "Social_media_links": {
                "Google Scholar": "https://scholar.google.com/citations?user=CXHND6AAAAAJ&hl=en",
                "Research Gate": "https://www.researchgate.net/profile/Mary-Joans",
                "Orchid Profile": "https://orcid.org/0009-0008-2908-5438",
                "Scopus": ".https://www.scopus.com/authid/detail.uri?authorId=54917116200"
            }
        },
        {
        
            "Name": "Dr. RAJESWARAN ",
            "Unique_id": "VEC-012-01-96",
            "Qualification":["M.sc","M.Phil","PhD"],
            "Hod_message": "Welcome to the Mathematics Department!",
            "Image": "vec pics/Dr. S.R - Prof. Rajeswaran. S Prof and Head - Maths.JPG",  # Path to the image
            "Social_media_links": {
                "LinkedIn": "http://www.linkedin.com/in/rajeswaran-subramani-03b61349",
                "Google Scholar": "https://scholar.google.com/citations?hl=en&user=hLT4dVIAAAAJ",
                "Research Gate": "https://www.researchgate.net/profile/Rajeswaran-Subramani",
                "Scopus": "https://www.scopus.com/authid/detail.uri?authorId=56049208900"
            }
        },


        {
        
            "Name": "JEBAMALAR",
            "Unique_id": "VEC-004-01-145",
            "Qualification":["M.E","PhD"],
            "Hod_message": "Welcome to the Civil Engineering Department!",
            "Image": "vec pics/Jebamalar - Dr.A.Jebamalar Prof & Head CIVIL.jpg",
            "Social_media_links": {
                "LinkedIn": "https://www.linkedin.com/in/jebamalar-abraham-986a35203/",
                "Google Scholar": "https://scholar.google.com/citations?hl=en&user=zMX3IjQAAAAJ",
                "Scopus": "https://www.scopus.com/authid/detail.uri?authorId=58322199400"
            }
        },

        {
            "Name": "Dr. M. RADHAKRISHNAN",
            "Unique_id": "VEC-002-01-102",
            "Qualification": ["M.E", "PhD"],
            "Hod_message": "Welcome to the Automobile Engineering Department!",
            "Image": "vec pics/Dr.RadhaKrishnan - Dr.M.Radhakrishnan Prof & Head Auto.jpg",
            "Social_media_links": {
                "LinkedIn": "https://www.linkedin.com/in/m-radhakrishnan/",
                "Google Scholar": "https://scholar.google.com/citations?user=mRadhaKrishnan&hl=en",
                "Research Gate": "https://www.researchgate.net/profile/M-Radhakrishnan",
                "Scopus": "https://www.scopus.com/authid/detail.uri?authorId=58322199455"
            }
        },
        {
            "Name": "Dr. S. BALAKRISHNAN",
            "Unique_id": "VEC-003-01-110",
            "Qualification": ["M.Sc", "PhD"],
            "Hod_message": "Welcome to the Chemistry Department!",
            "Image": "vec pics/Dr.Balakrishnan - Dr.S.Balakrishnan Prof & Head Chemistry.jpg",
            "Social_media_links": {
                "LinkedIn": "https://www.linkedin.com/in/s-balakrishnan-03b61349/",
                "Google Scholar": "https://scholar.google.com/citations?user=sBalakrishnan&hl=en",
                "Scopus": "https://www.scopus.com/authid/detail.uri?authorId=57349207800"
            }
        },
        {
            "Name": "Dr. A. MURUGAN",
            "Unique_id": "VEC-007-01-125",
            "Qualification": ["M.E", "PhD"],
            "Hod_message": "Welcome to the Electrical & Electronics Engineering Department!",
            "Image": "vec pics/Dr.Murugan - Dr.A.Murugan Prof & Head EEE.jpg",
            "Social_media_links": {
                "LinkedIn": "https://www.linkedin.com/in/a-murugan/",
                "Google Scholar": "https://scholar.google.com/citations?user=aMurugan&hl=en",
                "Scopus": "https://www.scopus.com/authid/detail.uri?authorId=57194019400"
            }
        },
        {
            "Name": "Dr. K. VELMURUGAN",
            "Unique_id": "VEC-008-01-130",
            "Qualification": ["M.E", "PhD"],
            "Hod_message": "Welcome to the Electronics & Instrumentation Engineering Department!",
            "Image": "vec pics/Dr.VelMurugan - Dr.K.VelMurugan Prof & Head EIE.jpg",
            "Social_media_links": {
                "LinkedIn": "https://www.linkedin.com/in/k-velmurugan/",
                "Google Scholar": "https://scholar.google.com/citations?user=kVelmurugan&hl=en",
                "Research Gate": "https://www.researchgate.net/profile/K-Velmurugan",
                "Scopus": "https://www.scopus.com/authid/detail.uri?authorId=57930299400"
            }
        },
        {
            "Name": "Dr. K. NAGARAJAN",
            "Unique_id": "VEC-005-01-120",
            "Qualification": ["M.E", "PhD"],
            "Hod_message": "Welcome to the Computer Science & Engineering Department!",
            "Image": "vec pics/Dr.Nagarajan - Dr.K.Nagarajan Prof & Head CSE.jpg",
            "Social_media_links": {
                "LinkedIn": "https://www.linkedin.com/in/k-nagarajan/",
                "Google Scholar": "https://scholar.google.com/citations?user=kNagarajan&hl=en",
                "Scopus": "https://www.scopus.com/authid/detail.uri?authorId=56140900400"
            }
        },
        {
            "Name": "Dr. S. MANOHARAN",
            "Unique_id": "VEC-006-01-135",
            "Qualification": ["M.E", "PhD"],
            "Hod_message": "Welcome to the Computer Science and Engineering (Cyber Security) Department!",
            "Image": "vec pics/Dr.Manoharan - Dr.S.Manoharan Prof & Head CSE-Cyber.jpg",
            "Social_media_links": {
                "LinkedIn": "https://www.linkedin.com/in/s-manoharan/",
                "Google Scholar": "https://scholar.google.com/citations?user=sManoharan&hl=en",
                "Research Gate": "https://www.researchgate.net/profile/S-Manoharan",
                "Scopus": "https://www.scopus.com/authid/detail.uri?authorId=57328209500"
            }
        },
        {
            "Name": "Dr. S. PRAVEENA",
            "Unique_id": "VEC-010-01-140",
            "Qualification": ["M.A", "PhD"],
            "Hod_message": "Welcome to the English Department!",
            "Image": "vec pics/Dr.Praveena - Dr.S.Praveena Prof & Head English.jpg",
            "Social_media_links": {
                "LinkedIn": "https://www.linkedin.com/in/s-praveena/",
                "Google Scholar": "https://scholar.google.com/citations?user=sPraveena&hl=en"
            }
        },
        {
            "Name": "Dr. S. GANESAN",
            "Unique_id": "VEC-011-01-150",
            "Qualification": ["M.E", "PhD"],
            "Hod_message": "Welcome to the Information Technology Department!",
            "Image": "vec pics/Dr.Ganesan - Dr.S.Ganesan Prof & Head IT.jpg",
            "Social_media_links": {
                "LinkedIn": "https://www.linkedin.com/in/s-ganesan/",
                "Google Scholar": "https://scholar.google.com/citations?user=sGanesan&hl=en",
                "Research Gate": "https://www.researchgate.net/profile/S-Ganesan",
                "Scopus": "https://www.scopus.com/authid/detail.uri?authorId=56829630300"
            }
        },
        {
            "Name": "Dr. R. SENTHIL",
            "Unique_id": "VEC-013-01-160",
            "Qualification": ["M.E", "PhD"],
            "Hod_message": "Welcome to the Mechanical Engineering Department!",
            "Image": "vec pics/Dr.Senthil - Dr.R.Senthil Prof & Head Mechanical.jpg",
            "Social_media_links": {
                "LinkedIn": "https://www.linkedin.com/in/r-senthil/",
                "Google Scholar": "https://scholar.google.com/citations?user=rSenthil&hl=en",
                "Scopus": "https://www.scopus.com/authid/detail.uri?authorId=56120129400"
            }
        }
    ]

    hod_collection.insert_many(departments)
    print("HOD documents inserted successfully.")

def insert_infrastructure_data():
    collection = db["infrastructure"]


    documents = [
        {
            "dept_id": 1,
            "infrastructure_images": [
                {"image_path": "path/to/image1_1.jpg", "image_name": "Image 1_1", "image_content": "Description of Image 1_1"},
                {"image_path": "path/to/image1_2.jpg", "image_name": "Image 1_2", "image_content": "Description of Image 1_2"},
                {"image_path": "path/to/image1_3.jpg", "image_name": "Image 1_3", "image_content": "Description of Image 1_3"},
                {"image_path": "path/to/image1_4.jpg", "image_name": "Image 1_4", "image_content": "Description of Image 1_4"},
                {"image_path": "path/to/image1_5.jpg", "image_name": "Image 1_5", "image_content": "Description of Image 1_5"}
            ]
        },
        {
            "dept_id": 2,
            "infrastructure_images": [
                {"image_path": "path/to/image2_1.jpg", "image_name": "Image 2_1", "image_content": "Description of Image 2_1"},
                {"image_path": "path/to/image2_2.jpg", "image_name": "Image 2_2", "image_content": "Description of Image 2_2"},
                {"image_path": "path/to/image2_3.jpg", "image_name": "Image 2_3", "image_content": "Description of Image 2_3"},
                {"image_path": "path/to/image2_4.jpg", "image_name": "Image 2_4", "image_content": "Description of Image 2_4"},
                {"image_path": "path/to/image2_5.jpg", "image_name": "Image 2_5", "image_content": "Description of Image 2_5"}
            ]
        },
        {
            "dept_id": 3,
            "infrastructure_images": [
                {"image_path": "path/to/image3_1.jpg", "image_name": "Image 3_1", "image_content": "Description of Image 3_1"},
                {"image_path": "path/to/image3_2.jpg", "image_name": "Image 3_2", "image_content": "Description of Image 3_2"},
                {"image_path": "path/to/image3_3.jpg", "image_name": "Image 3_3", "image_content": "Description of Image 3_3"},
                {"image_path": "path/to/image3_4.jpg", "image_name": "Image 3_4", "image_content": "Description of Image 3_4"},
                {"image_path": "path/to/image3_5.jpg", "image_name": "Image 3_5", "image_content": "Description of Image 3_5"}
            ]
        },
        {
            "dept_id": 4,
            "infrastructure_images": [
                {"image_path": "path/to/image4_1.jpg", "image_name": "Image 4_1", "image_content": "Description of Image 4_1"},
                {"image_path": "path/to/image4_2.jpg", "image_name": "Image 4_2", "image_content": "Description of Image 4_2"},
                {"image_path": "path/to/image4_3.jpg", "image_name": "Image 4_3", "image_content": "Description of Image 4_3"},
                {"image_path": "path/to/image4_4.jpg", "image_name": "Image 4_4", "image_content": "Description of Image 4_4"},
                {"image_path": "path/to/image4_5.jpg", "image_name": "Image 4_5", "image_content": "Description of Image 4_5"}
            ]
        },
        {
            "dept_id": 5,
            "infrastructure_images": [
                {"image_path": "path/to/image5_1.jpg", "image_name": "Image 5_1", "image_content": "Description of Image 5_1"},
                {"image_path": "path/to/image5_2.jpg", "image_name": "Image 5_2", "image_content": "Description of Image 5_2"},
                {"image_path": "path/to/image5_3.jpg", "image_name": "Image 5_3", "image_content": "Description of Image 5_3"},
                {"image_path": "path/to/image5_4.jpg", "image_name": "Image 5_4", "image_content": "Description of Image 5_4"},
                {"image_path": "path/to/image5_5.jpg", "image_name": "Image 5_5", "image_content": "Description of Image 5_5"}
            ]
        },
        {
            "dept_id": 6,
            "infrastructure_images": [
                {"image_path": "path/to/image6_1.jpg", "image_name": "Image 6_1", "image_content": "Description of Image 6_1"},
                {"image_path": "path/to/image6_2.jpg", "image_name": "Image 6_2", "image_content": "Description of Image 6_2"},
                {"image_path": "path/to/image6_3.jpg", "image_name": "Image 6_3", "image_content": "Description of Image 6_3"},
                {"image_path": "path/to/image6_4.jpg", "image_name": "Image 6_4", "image_content": "Description of Image 6_4"},
                {"image_path": "path/to/image6_5.jpg", "image_name": "Image 6_5", "image_content": "Description of Image 6_5"}
            ]
        },
        {
            "dept_id": 7,
            "infrastructure_images": [
                {"image_path": "path/to/image7_1.jpg", "image_name": "Image 7_1", "image_content": "Description of Image 7_1"},
                {"image_path": "path/to/image7_2.jpg", "image_name": "Image 7_2", "image_content": "Description of Image 7_2"},
                {"image_path": "path/to/image7_3.jpg", "image_name": "Image 7_3", "image_content": "Description of Image 7_3"},
                {"image_path": "path/to/image7_4.jpg", "image_name": "Image 7_4", "image_content": "Description of Image 7_4"},
                {"image_path": "path/to/image7_5.jpg", "image_name": "Image 7_5", "image_content": "Description of Image 7_5"}
            ]
        },
        {
            "dept_id": 8,
            "infrastructure_images": [
                {"image_path": "path/to/image8_1.jpg", "image_name": "Image 8_1", "image_content": "Description of Image 8_1"},
                {"image_path": "path/to/image8_2.jpg", "image_name": "Image 8_2", "image_content": "Description of Image 8_2"},
                {"image_path": "path/to/image8_3.jpg", "image_name": "Image 8_3", "image_content": "Description of Image 8_3"},
                {"image_path": "path/to/image8_4.jpg", "image_name": "Image 8_4", "image_content": "Description of Image 8_4"},
                {"image_path": "path/to/image8_5.jpg", "image_name": "Image 8_5", "image_content": "Description of Image 8_5"}
            ]
        },
        {
            "dept_id": 9,
            "infrastructure_images": [
                {"image_path": "path/to/image9_1.jpg", "image_name": "Image 9_1", "image_content": "Description of Image 9_1"},
                {"image_path": "path/to/image9_2.jpg", "image_name": "Image 9_2", "image_content": "Description of Image 9_2"},
                {"image_path": "path/to/image9_3.jpg", "image_name": "Image 9_3", "image_content": "Description of Image 9_3"},
                {"image_path": "path/to/image9_4.jpg", "image_name": "Image 9_4", "image_content": "Description of Image 9_4"},
                {"image_path": "path/to/image9_5.jpg", "image_name": "Image 9_5", "image_content": "Description of Image 9_5"}
            ]
        },
        {
            "dept_id": 10,
            "infrastructure_images": [
                {"image_path": "path/to/image10_1.jpg", "image_name": "Image 10_1", "image_content": "Description of Image 10_1"},
                {"image_path": "path/to/image10_2.jpg", "image_name": "Image 10_2", "image_content": "Description of Image 10_2"},
                {"image_path": "path/to/image10_3.jpg", "image_name": "Image 10_3", "image_content": "Description of Image 10_3"},
                {"image_path": "path/to/image10_4.jpg", "image_name": "Image 10_4", "image_content": "Description of Image 10_4"},
                {"image_path": "path/to/image10_5.jpg", "image_name": "Image 10_5", "image_content": "Description of Image 10_5"}
            ]
        },
        {
            "dept_id": 11,
            "infrastructure_images": [
                {"image_path": "path/to/image11_1.jpg", "image_name": "Image 11_1", "image_content": "Description of Image 11_1"},
                {"image_path": "path/to/image11_2.jpg", "image_name": "Image 11_2", "image_content": "Description of Image 11_2"},
                {"image_path": "path/to/image11_3.jpg", "image_name": "Image 11_3", "image_content": "Description of Image 11_3"},
                {"image_path": "path/to/image11_4.jpg", "image_name": "Image 11_4", "image_content": "Description of Image 11_4"},
                {"image_path": "path/to/image11_5.jpg", "image_name": "Image 11_5", "image_content": "Description of Image 11_5"}
            ]
        },
        {
            "dept_id": 12,
            "infrastructure_images": [
                {"image_path": "path/to/image12_1.jpg", "image_name": "Image 12_1", "image_content": "Description of Image 12_1"},
                {"image_path": "path/to/image12_2.jpg", "image_name": "Image 12_2", "image_content": "Description of Image 12_2"},
                {"image_path": "path/to/image12_3.jpg", "image_name": "Image 12_3", "image_content": "Description of Image 12_3"},
                {"image_path": "path/to/image12_4.jpg", "image_name": "Image 12_4", "image_content": "Description of Image 12_4"},
                {"image_path": "path/to/image12_5.jpg", "image_name": "Image 12_5", "image_content": "Description of Image 12_5"}
            ]
        },
        {
            "dept_id": 13,
            "infrastructure_images": [
                {"image_path": "path/to/image13_1.jpg", "image_name": "Image 13_1", "image_content": "Description of Image 13_1"},
                {"image_path": "path/to/image13_2.jpg", "image_name": "Image 13_2", "image_content": "Description of Image 13_2"},
                {"image_path": "path/to/image13_3.jpg", "image_name": "Image 13_3", "image_content": "Description of Image 13_3"},
                {"image_path": "path/to/image13_4.jpg", "image_name": "Image 13_4", "image_content": "Description of Image 13_4"},
                {"image_path": "path/to/image13_5.jpg", "image_name": "Image 13_5", "image_content": "Description of Image 13_5"}
            ]
        },
        {
            "dept_id": 14,
            "infrastructure_images": [
                {"image_path": "path/to/image14_1.jpg", "image_name": "Image 14_1", "image_content": "Description of Image 14_1"},
                {"image_path": "path/to/image14_2.jpg", "image_name": "Image 14_2", "image_content": "Description of Image 14_2"},
                {"image_path": "path/to/image14_3.jpg", "image_name": "Image 14_3", "image_content": "Description of Image 14_3"},
                {"image_path": "path/to/image14_4.jpg", "image_name": "Image 14_4", "image_content": "Description of Image 14_4"},
                {"image_path": "path/to/image14_5.jpg", "image_name": "Image 14_5", "image_content": "Description of Image 14_5"}
            ]
        },
        {
            "dept_id": 15,
            "infrastructure_images": [
                {"image_path": "path/to/image15_1.jpg", "image_name": "Image 15_1", "image_content": "Description of Image 15_1"},
                {"image_path": "path/to/image15_2.jpg", "image_name": "Image 15_2", "image_content": "Description of Image 15_2"},
                {"image_path": "path/to/image15_3.jpg", "image_name": "Image 15_3", "image_content": "Description of Image 15_3"},
                {"image_path": "path/to/image15_4.jpg", "image_name": "Image 15_4", "image_content": "Description of Image 15_4"},
                {"image_path": "path/to/image15_5.jpg", "image_name": "Image 15_5", "image_content": "Description of Image 15_5"}
            ]
        }
    ]
    collection.insert_many(documents)
    print("Infrastructure documents inserted successfully.")

insert_department_data()
insert_hod_datas()
insert_infrastructure_data()