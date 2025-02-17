import requests
import os
import psycopg2
from dotenv import load_dotenv
from time import sleep

# Load API key from .env
load_dotenv()
API_KEY = os.getenv("CFB_API_KEY")

if not API_KEY:
    raise ValueError("API Key not found! Make sure to set CFB_API_KEY in .env")

# Database connection settings
DB_PARAMS = {
    "dbname": "sports_agency",
    "user": "postgres",  # Use your actual PostgreSQL username
    "password": "fleish00",  # Use your actual PostgreSQL password
    "host": "localhost",
    "port": "5432"
}

# API Endpoint
url = "https://api.collegefootballdata.com/roster"

# Seasons to fetch
years = [2019, 2020, 2021, 2022, 2023, 2024]

# Headers for authentication
headers = {"Authorization": f"Bearer {API_KEY}"}


def get_power5_teams(cur):
    """Retrieve Power 5 teams from PostgreSQL."""
    cur.execute("SELECT team_id, name FROM teams;")
    return cur.fetchall()  # Returns list of (team_id, team_name) tuples


def insert_player(cur, player):
    """Insert player into athletes table if they don't exist."""
    cur.execute("""
        INSERT INTO athletes (athlete_id, first_name, last_name, home_city, home_state, position)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (athlete_id) DO NOTHING;
    """, (player["id"], player["first_name"], player["last_name"],
          player.get("home_city"), player.get("home_state"), player["position"]))


def insert_roster_entry(cur, player, team_id, year):
    """Insert player's team-year relationship into rosters table."""
    cur.execute("""
        INSERT INTO rosters (athlete_id, team_id, year)
        VALUES (%s, %s, %s)
        ON CONFLICT DO NOTHING;
    """, (player["id"], team_id, year))


def fetch_and_store_rosters():
    """Fetch rosters for all Power 5 teams (2019-2024) and store in PostgreSQL."""
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()

        # Get all Power 5 teams
        teams = get_power5_teams(cur)
        print(f"✅ Found {len(teams)} Power 5 teams in database.")

        total_requests = 0

        for team_id, team_name in teams:
            for year in years:
                if total_requests >= 500:  # Stay within API limit
                    print("🚨 API request limit reached (500). Stopping.")
                    conn.commit()
                    cur.close()
                    conn.close()
                    return

                print(f"📡 Fetching {team_name} roster for {year}...")
                params = {"team": team_name, "year": year}
                response = requests.get(url, headers=headers, params=params)

                if response.status_code == 200:
                    roster_data = response.json()
                    print(f"✅ {team_name} {year}: {len(roster_data)} players retrieved.")

                    for player in roster_data:
                        insert_player(cur, player)
                        insert_roster_entry(cur, player, team_id, year)

                    total_requests += 1
                    sleep(1)  # Small delay to avoid hitting rate limits

                else:
                    print(f"❌ API Error {response.status_code} for {team_name} {year}: {response.text}")

        # Commit all changes
        conn.commit()
        print("✅ All rosters successfully inserted into PostgreSQL!")

        # Close DB connection
        cur.close()
        conn.close()

    except Exception as e:
        print(f"❌ Error inserting rosters: {e}")


if __name__ == "__main__":
    fetch_and_store_rosters()
