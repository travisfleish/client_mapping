import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# PostgreSQL connection settings
DB_PARAMS = {
    "dbname": "sports_agency",
    "user": "postgres",
    "password": "fleish00",  # Change to your actual password
    "host": "localhost",
    "port": "5432"
}

def fetch_power5_teams():
    """Retrieve Power 5 teams from PostgreSQL"""
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()

        # Query for all teams
        cur.execute("SELECT name FROM teams;")
        teams = [row[0] for row in cur.fetchall()]

        # Close connection
        cur.close()
        conn.close()

        print(f"Total Power 5 Teams Retrieved: {len(teams)}")
        return teams

    except Exception as e:
        print(f"Error fetching teams: {e}")
        return []

if __name__ == "__main__":
    power5_teams = fetch_power5_teams()
    print(power5_teams)  # Print the list of teams
