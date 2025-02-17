import requests
import os
import psycopg2
from dotenv import load_dotenv

# Load API key from .env
load_dotenv()
API_KEY = os.getenv("CFB_API_KEY")

if not API_KEY:
    raise ValueError("API Key not found! Make sure to set CFB_API_KEY in .env")

# Database connection settings
DB_PARAMS = {
    "dbname": "sports_agency",
    "user": "postgres",  # Change if needed
    "password": "fleish00",  # Change to your actual password
    "host": "localhost",
    "port": "5432"
}

# API Endpoint
url = "https://api.collegefootballdata.com/roster"

# Test Team & Year
team_name = "Alabama"
year = 2023

# Headers for authentication
headers = {"Authorization": f"Bearer {API_KEY}"}

def insert_player(cur, player):
    """Insert player into athletes table if they don't exist."""
    cur.execute("""
        INSERT INTO athletes (athlete_id, first_name, last_name, home_city, home_state, position)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (athlete_id) DO NOTHING;
    """, (player["id"], player["first_name"], player["last_name"],
          player.get("home_city"), player.get("home_state"), player["position"]))

def insert_roster_entry(cur, player, team_id, year):
    """Insert player's team affiliation into rosters table."""
    cur.execute("""
        INSERT INTO rosters (athlete_id, team_id, year)
        VALUES (%s, %s, %s)
        ON CONFLICT DO NOTHING;
    """, (player["id"], team_id, year))

def get_team_id(cur, team_name):
    """Retrieve the team ID from the teams table."""
    cur.execute("SELECT team_id FROM teams WHERE name = %s;", (team_name,))
    result = cur.fetchone()
    return result[0] if result else None

def fetch_and_store_roster():
    """Fetch a single team's roster and store it in PostgreSQL."""
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()

        # Get team ID
        team_id = get_team_id(cur, team_name)
        if not team_id:
            print(f"❌ Team '{team_name}' not found in teams table!")
            return

        # Fetch roster from API
        params = {"team": team_name, "year": year}
        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            roster_data = response.json()
            print(f"✅ {team_name} {year}: {len(roster_data)} players retrieved.")

            for player in roster_data:
                insert_player(cur, player)
                insert_roster_entry(cur, player, team_id, year)

            # Commit changes
            conn.commit()
            print("✅ Data successfully inserted into PostgreSQL!")

        else:
            print(f"❌ API Error {response.status_code}: {response.text}")

        # Close DB connection
        cur.close()
        conn.close()

    except Exception as e:
        print(f"❌ Error inserting roster: {e}")

if __name__ == "__main__":
    fetch_and_store_roster()
