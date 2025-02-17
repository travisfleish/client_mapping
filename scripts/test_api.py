import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Retrieve API key from .env
API_KEY = os.getenv("CFB_API_KEY")

if not API_KEY:
    raise ValueError("API Key not found! Make sure to set CFB_API_KEY in .env")

# API Endpoint for teams
url = "https://api.collegefootballdata.com/teams"

# Headers with authentication
headers = {
    "Authorization": f"Bearer {API_KEY}"
}

# Make the API request
response = requests.get(url, headers=headers)

if response.status_code == 200:
    teams_data = response.json()

    # Filter for only Power 5 schools
    power5_conferences = {"SEC", "Big Ten", "ACC", "Big 12", "Pac-12"}
    power5_teams = [team for team in teams_data if team.get("conference") in power5_conferences]

    # Print results
    print(f"Total Power 5 Teams: {len(power5_teams)}")
    for team in power5_teams:
        print(f"{team['school']} ({team['conference']})")

else:
    print(f"Error {response.status_code}: {response.text}")