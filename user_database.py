import os
import certifi
from pymongo import MongoClient

# Load environment variables
import dotenv
dotenv.load_dotenv()

# MongoDB configuration
MONGODB_URI = os.getenv("MONGO_CLIENT")

# MongoDB connection
ca_cert_path = certifi.where()
client = MongoClient(MONGODB_URI, tlsCAFile=ca_cert_path)
db = client["elyufbot"]
collection = db["users"]
for db_name in client.list_database_names():
    print(db_name)

# Global variables to store user data
registered_users = []
user_data = {}

# Load registered users from MongoDB
def load_registered_users():
    global registered_users, user_data
    registered_users = [doc["_id"] for doc in collection.find()]
    user_data = {doc["_id"]: doc for doc in collection.find()}
    print("Registered Users successfully loaded!")
    
load_registered_users()

# # Load the last 150 registered users from MongoDB
# def load_last_150_registered_users():
#     try:
#         # Assuming the documents have a 'signup_datetime' field
#         last_150_users = collection.find().sort("signup_datetime", -1).limit(150)
#         for user in last_150_users:
#             print(user)
#     except Exception as e:
#         print(f"An error occurred: {e}")
#
# if __name__ == "__main__":
#     load_last_150_registered_users()