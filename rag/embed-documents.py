# from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_google_vertexai import VertexAIEmbeddings
from langchain.schema import Document

import os
import json
from dotenv import load_dotenv
from mongodb_database import *

# Load environment variables
load_dotenv()

# Authenticate Google Cloud service account
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/Users/mukhsinmukhtorov/Desktop/Elyuf/rag/google-services/eyuf-rag-427520-319f41429e2b.json"

# Function to load JSON data
def load_json_data(file_path):
    with open(file_path, 'r', encoding="utf-8") as file:
        return json.load(file)

# Load all JSON files within a specified directory
directory_path = "/Users/mukhsinmukhtorov/Desktop/Elyuf/data/json_data"
json_files = [f for f in os.listdir(directory_path) if f.endswith('.json')]

documents = []
for file in json_files:
    file_path = os.path.join(directory_path, file)
    data = load_json_data(file_path)
    
    source = data.get('source') # need this to link to every ranks to clearify the source
    
    print(f"\nProcessing file: {file}")
    print(f"Source: {source}")
    
    if 'data' not in data:
        print(f"Warning: 'data' key not found in {file}")
        break
    
    total_universities = 0
    universities_in_file = len(data['data'])
    total_universities += universities_in_file
    print(f"Number of universities in this file: {universities_in_file}")
    
    
    for item in data.get('data', []):
            try:
                text = f" Source: {source}, Rank: {item['rank']}, University: {item['university']}, Country: {item['country']}"
                metadata = {
                    # its value is used as-is in JSON files
                    'source': item.get('source'),
                    'rank': item.get('rank'),
                    "university": item.get('university'),
                    "country": item.get('country')
                }
                # Create a Document object 
                doc = Document(page_content=text, metadata=metadata)
                documents.append(doc) # Add the document to the list of documents
            except KeyError as e:
                print(f"Error processing item in {file}: Missing key {e}")
                print(f"Problematic item: {item}")
            except Exception as e:
                print(f"Unexpected error processing item in {file}: {e}")
                print(f"Problematic item: {item}")

print(f"\nTotal universities across all files: {total_universities}")
print(f"Loaded {len(documents)} university rankings from JSON files.")
print(f"Number of processed files: {len(json_files)}")


if total_universities != len(documents):
    print(f"Warning: Mismatch between total universities ({total_universities}) and loaded documents ({len(documents)})")

# Split the docs into chunks
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=200)
split_docs = text_splitter.split_documents(documents)
print(f"Splitted documents into {len(split_docs)} chunks")

# Connect to MongoDB
client = client
db = db
COLLECTION_NAME = collection

# Instantiate VertexAIEmbeddings with a specific model name
embeddings = VertexAIEmbeddings(
    model_name="text-embedding-004"
)

# Instantiate MongoDBAtlasVectorSearch
vector_search = MongoDBAtlasVectorSearch(
    embedding=embeddings,
    collection=COLLECTION_NAME,
    index_name=INDEX_NAME,
)

# Insert the documents into the MongoDB Atlas Vector Search
result = vector_search.add_documents(split_docs)
print(f"Inserted {len(result)} documents into MongoDB Atlas Vector Search")

if __name__ == "__main__":
    import sys
    sys.exit(0)