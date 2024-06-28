import os
import json
from dotenv import load_dotenv

load_dotenv()

# Function to load JSON data
def load_json_data(file_path):
    with open(file_path, 'r', encoding="utf-8") as file:
        return json.load(file)

directory_path = "/Users/mukhsinmukhtorov/Desktop/Elyuf/data"
json_files = [f for f in os.listdir(directory_path) if f.endswith('.json')]

total_universities = 0

for file in json_files:
    file_path = os.path.join(directory_path, file)  # Use os.path.join to concatenate paths correctly
    data = load_json_data(file_path)
    
    if 'data' not in data:
        print(f"Warning: 'data' key not found in {file}")
        continue
    
    universities_in_file = len(data['data']['university'])
    total_universities += universities_in_file
    print(f"Number of universities in {file}: {universities_in_file}")

print(f"Total number of universities in all JSON files: {total_universities}")

if __name__ == "__main__":
    pass