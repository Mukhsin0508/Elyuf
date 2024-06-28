import os
import certifi
from pymongo import MongoClient
import dotenv

# Load environment variables
dotenv.load_dotenv()

# MongoDB configuration
MONGODB_URI = os.getenv("MONGO_CLIENT")
DATABASE_NAME = os.getenv("DATABASE_NAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")
INDEX_NAME = os.getenv("INDEX_NAME")

# MongoDB connection
ca_cert_path = certifi.where()
client = MongoClient(MONGODB_URI, tlsCAFile=ca_cert_path)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

# Print Existing database_names
for db_name in client.list_database_names():
    print(db_name)
    
# count = collection.count_documents({})
# print(f"Number of documents in the collection: {count}")

# # Clear the collection
# collection.delete_many({})
# print("Collections has been cleared.")

# Count unique university names
# unique_universities_count = collection.distinct("university")
# print(f"Number of unique universities: {len(unique_universities_count)}")

if __name__ == "__main__":
    pass



# For Atlas Cluster Vector Search Configurations
    """
    {
  "fields": [
    {
      "type": "vector",
      "path": "embedding",
      "numDimensions": 768,
      "similarity": "cosine" or "euclidean" 
    }
  ]
}
    """