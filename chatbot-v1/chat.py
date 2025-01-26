from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone , ServerlessSpec

def fetch_all_data(uri, db_name):
    client = MongoClient(uri)
    db = client[db_name]

    all_texts = []
    all_metadata = []

    for collection_name in db.list_collection_names():
        print(f"Fetching data from collection: {collection_name}")
        collection = db[collection_name]
        data = list(collection.find())
        for doc in data:
            doc_metadata = {"collection": collection_name, "_id": str(doc["_id"])}
            doc_text = " ".join(
                [str(value) for key, value in doc.items() if isinstance(value, str)]
            )
            all_texts.append(doc_text)
            all_metadata.append(doc_metadata)

    return all_texts, all_metadata

def generate_embeddings(texts, model_name="all-MiniLM-L6-v2"):
    model = SentenceTransformer(model_name)
    embeddings = model.encode(texts, show_progress_bar=True)
    return embeddings

def upload_to_pinecone(embeddings, metadata, index_name, pinecone_api_key, index_host):
    pc = Pinecone(api_key=pinecone_api_key)
    if index_name not in pc.list_indexes().names():
        dimension = len(embeddings[0])
        pc.create_index(
            name=index_name,
            dimension=dimension,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-west-1"
            )
        )

    index = pc.Index(host=index_host)
    upserts = [
        {"id": str(i), "values": embedding.tolist(), "metadata": metadata[i]}
        for i, embedding in enumerate(embeddings)
    ]
    index.upsert(vectors=upserts)

    print("Data successfully uploaded to Pinecone!")


def main():
    mongo_uri = "mongodb://localhost:27017/"
    db_name = "VEC"
    index_name = "vec-data"

    pinecone_api_key = 'pcsk_5XXpmL_TJeSzwPSbUNL1i33viwUUugZwqnkVUQd6ZzpmMcQmEsZiS1pR64jWX9oGw1sFzR'
    index_host = 'https://vec-data-mkz5a3h.svc.aped-4627-b74a.pinecone.io'

    model_name = "all-MiniLM-L6-v2"
    print("Fetching data from MongoDB...")
    texts, metadata = fetch_all_data(mongo_uri, db_name)

    if not texts:
        print("No data found in the database.")
        return

    print(f"Generating embeddings with model: {model_name}...")
    embeddings = generate_embeddings(texts, model_name)

    print("Uploading data to Pinecone...")
    upload_to_pinecone(embeddings, metadata, index_name, pinecone_api_key, index_host)

if __name__ == "__main__":
    main()
