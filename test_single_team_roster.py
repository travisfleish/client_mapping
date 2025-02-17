import requests
import os
from dotenv import load_dotenv

# Load API key from .env
load_dotenv()
API_KEY = os.getenv("CFB_API_KEY")

if not API_KEY:
    raise ValueError("API Key not found! Make sure to set CFB_API_KEY in .env")

# API Endpoint
url = "https://api.collegefootballdata.com/roster"

# Team and years to test
team_name = "Alabama"
years = [2019, 2020, 2021, 2022, 2023, 2024]  # 5-year test

# Headers for authentication
headers = {
    "Authorization": f"Bearer {API_KEY}"
}

# Fetch rosters for each year
for year in years:
    params = {"team": team_name, "year": year}
    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        print(f"Year: {year} | Total Players: {len(data)}")
        if data:
            print(f"Sample Player: {data[0]}")  # Print first player for reference
    else:
        print(f"Error {response.status_code} for {team_name} in {year}: {response.text}")
