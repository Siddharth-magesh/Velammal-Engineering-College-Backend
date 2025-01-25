from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import pickle
import os

def fetch_all_data(uri, db_name):
    """
    Fetch all data from all collections in the specified database.
    Returns a list of concatenated text for embedding and corresponding document metadata.
    """
    client = MongoClient(uri)
    db = client[db_name]

    all_texts = []
    all_metadata = []

    # Iterate through all collections
    for collection_name in db.list_collection_names():
        print(f"Fetching data from collection: {collection_name}")
        collection = db[collection_name]

        # Fetch all documents in the collection
        data = list(collection.find())

        # Extract text and metadata from documents
        for doc in data:
            doc_metadata = {"collection": collection_name, "_id": str(doc["_id"])}
            # Combine all text fields into one string
            doc_text = " ".join(
                [str(value) for key, value in doc.items() if isinstance(value, str)]
            )

            all_texts.append(doc_text)
            all_metadata.append(doc_metadata)

    return all_texts, all_metadata

def generate_embeddings(texts, model_name="all-MiniLM-L6-v2"):
    """
    Generate embeddings using a local pre-trained SentenceTransformer model.
    """
    model = SentenceTransformer(model_name)
    embeddings = model.encode(texts, show_progress_bar=True)
    return embeddings

def create_faiss_index(embeddings, save_path="faiss_index.bin"):
    """
    Create and save a FAISS index from the given embeddings.
    """
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings))
    faiss.write_index(index, save_path)
    return index

def save_metadata(metadata, save_path="metadata.pkl"):
    """
    Save metadata mapping to a file.
    """
    with open(save_path, "wb") as f:
        pickle.dump(metadata, f)

def query_faiss_index(query, model, index_path, metadata_path, top_k=5):
    """
    Query the FAISS index for the nearest neighbors of a given query.
    """
    # Generate embedding for the query
    query_embedding = model.encode([query])

    # Load FAISS index and metadata
    index = faiss.read_index(index_path)
    with open(metadata_path, "rb") as f:
        metadata = pickle.load(f)

    # Perform FAISS search
    distances, indices = index.search(np.array(query_embedding), top_k)

    # Retrieve results
    results = [{"metadata": metadata[i], "distance": float(distances[0][idx])} for idx, i in enumerate(indices[0])]
    return results

def main():
    # MongoDB and embedding setup
    mongo_uri = "mongodb://localhost:27017/"
    db_name = "VEC"  # Replace with your database name
    index_path = "/faiss_index.bin"
    metadata_path = "/metadata.pkl"
    model_name = "all-MiniLM-L6-v2"  # You can choose other models like "multi-qa-mpnet-base-dot-v1"

    # Ensure the directory exists for saving files
    os.makedirs(os.path.dirname(index_path), exist_ok=True)

    # Step 1: Fetch all data from the database
    print("Fetching data from MongoDB...")
    texts, metadata = fetch_all_data(mongo_uri, db_name)

    if not texts:
        print("No data found in the database.")
        return

    # Step 2: Generate embeddings using local LLM
    print(f"Generating embeddings with model: {model_name}...")
    embeddings = generate_embeddings(texts, model_name)

    # Step 3: Create FAISS index and save
    print("Creating and saving FAISS index...")
    create_faiss_index(embeddings, index_path)

    # Step 4: Save metadata
    print("Saving metadata...")
    save_metadata(metadata, metadata_path)

    # Step 5: Query example
    query = "Sample query text"
    model = SentenceTransformer(model_name)  # Load the same model for querying
    print("Querying FAISS index...")
    results = query_faiss_index(query, model, index_path, metadata_path, top_k=5)
    print("Search Results:", results)

# Run the process
if __name__ == "__main__":
    main()
