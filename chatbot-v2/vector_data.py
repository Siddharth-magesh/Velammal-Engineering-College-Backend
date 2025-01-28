import os
from pymongo import MongoClient
from langchain.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document

def fetch_documents_from_mongodb(uri, database_name):
    client = MongoClient(uri)
    db = client[database_name]
    documents = []
    
    for collection_name in db.list_collection_names():
        collection = db[collection_name]
        for doc in collection.find():
            content = str(doc)
            documents.append(Document(page_content=content, metadata={"collection": collection_name}))
    
    return documents

def create_faiss_store(documents, embeddings_model):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    split_docs = text_splitter.split_documents(documents)
    faiss_store = FAISS.from_documents(split_docs, embeddings_model)
    return faiss_store

if __name__ == "__main__":
    MONGO_URI = "mongodb://localhost:27017"
    DATABASE_NAME = "VEC"

    print("Fetching documents from MongoDB...")
    documents = fetch_documents_from_mongodb(MONGO_URI, DATABASE_NAME)

    print("Creating embeddings and storing them in FAISS...")
    embeddings = OllamaEmbeddings(model="bge-large")
    faiss_store = create_faiss_store(documents, embeddings)

    print("Saving FAISS index to 'faiss_index' directory...")
    faiss_store.save_local("/home/server/Desktop/Velammal-Engineering-College-Backend/chatbot-v2/faiss_index")

    print("Reloading FAISS index...")
    new_vector_store = FAISS.load_local(
        "faiss_index", embeddings, allow_dangerous_deserialization=True
    )

    query = "example query to test"
    docs = new_vector_store.similarity_search(query, k=3)
    print("\nTop 3 similar documents:")
    for doc in docs:
        print(f"- Content: {doc.page_content[:200]}...")
        print(f"  Metadata: {doc.metadata}")