import json
import math
from pymongo import MongoClient

MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "VEC"
COLLECTION_NAMES = [
    "HODS", "Intakes", "MOUs", "admin_office", "all_forms", "alumni",
    "announcements", "banner", "committee", "curriculum",
    "curriculum_and_syllabus", "dean_and_associates", "department_activities",
    "department_research_Data", "events", "faculty_data", "iic",
    "infrastructure", "library", "naac", "nirf", "nba", "nss_data",
    "other_facilties", "overall_research", "placement_team",
    "placements_data", "principal_data", "regulation", "sidebar",
    "special_announcement", "sports_data", "staff_details",
    "student_activities", "support_staffs", "vision_and_mission", "yrc_data"
]
OUTPUT_FILE = "output.json"

def sanitize_document(doc):
    if isinstance(doc, dict):
        return {k: sanitize_document(v) for k, v in doc.items()}
    elif isinstance(doc, list):
        return [sanitize_document(v) for v in doc]
    elif isinstance(doc, float):
        if math.isnan(doc) or math.isinf(doc):
            return None
    return doc

def fetch_all_documents():
    try:
        client = MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        all_data = {}

        for collection_name in COLLECTION_NAMES:
            collection = db[collection_name]
            documents = list(collection.find())

            sanitized_documents = []
            for doc in documents:
                doc["_id"] = str(doc["_id"])
                sanitized_documents.append(sanitize_document(doc))  # Fix NaN/Infinity

            all_data[collection_name] = sanitized_documents

        # Write data to JSON
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(all_data, f, indent=4)

        print(f"Data successfully saved to {OUTPUT_FILE}")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        client.close()

# Run the function
fetch_all_documents()
