import json

def load_data():
    """Load data from JSON files.
    This file's code is used for loading data from JSON files in the data directory.
    but it is not used in the current implementation as the data is loaded from the database MongoDB."""
    try:
        with open("data/init-QS.json") as qs_file:
            qs_data = json.load(qs_file)["data"]
    except json.JSONDecodeError as e:
        print(f"Error loading init-QS.json: {e}")
        qs_data = []

    try:
        with open("data/init-Times.json") as times_file:
            times_data = json.load(times_file)["data"]
    except json.JSONDecodeError as e:
        print(f"Error loading init-Times.json: {e}")
        times_data = []

    try:
        with open("data/init-US&NEWS.json") as us_news_file:
            us_news_data = json.load(us_news_file)["data"]
    except json.JSONDecodeError as e:
        print(f"Error loading init-US&NEWS.json: {e}")
        us_news_data = [] 

    return qs_data, times_data, us_news_data, 

