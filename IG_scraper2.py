import psycopg2
import time
import os
import random
import re
import logging
from concurrent.futures import ThreadPoolExecutor
from serpapi import GoogleSearch

# PostgreSQL connection
conn = psycopg2.connect(
    dbname="sports_agency",
    user="postgres",
    password="fleish00",  # Change this if needed
    host="localhost",
    port="5432"
)
cursor = conn.cursor()

# SerpAPI Key (Replace with your actual key)
SERPAPI_KEY = "93aa46688ae211cc553920007426ee27dddf096e3fd2929a7176785d38fe11b0"

# Proxy List (Add your own proxies if needed)
PROXIES = [
    "http://proxy1.com:port",
    "http://proxy2.com:port",
    "http://proxy3.com:port"
]

# Logging setup
logging.basicConfig(
    filename="search_log.txt",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# Function to log search results
def log_result(status, first_name, last_name, handle):
    logging.info(f"{status}: {first_name} {last_name} -> {handle}")


# Function to fetch athletes from the database
def get_athletes(limit=50):
    cursor.execute("""
        SELECT DISTINCT ON (a.athlete_id) 
            a.athlete_id, a.first_name, a.last_name, t.name AS school_name
        FROM athletes a
        JOIN rosters r ON a.athlete_id = r.athlete_id
        JOIN teams t ON r.team_id = t.team_id
        WHERE a.instagram_handle IS NULL
        ORDER BY a.athlete_id, r.year DESC
        LIMIT %s;
    """, (limit,))
    return cursor.fetchall()


# Function to get a random proxy (optional)
def get_proxy():
    return random.choice(PROXIES)


# Function to search Instagram profiles using SerpAPI with retries
def search_instagram_handle(first_name, last_name, school_name, retries=1):
    query = f"{first_name} {last_name} {school_name} Instagram"

    for attempt in range(retries + 1):
        try:
            params = {
                "engine": "google",
                "q": query,
                "api_key": SERPAPI_KEY
            }

            search = GoogleSearch(params)
            results = search.get_dict()

            if "organic_results" in results:
                for result in results["organic_results"]:
                    title = result.get("title", "")
                    snippet = result.get("snippet", "")
                    link = result.get("link", "")

                    # Ignore Instagram explore/location pages
                    if "/explore/" in link or "/locations/" in link:
                        continue

                    # Extract handle from title (@username)
                    match = re.search(r"\(@([\w\d_.-]+)\)", title)
                    if match:
                        return match.group(1)

                    # Backup: Extract handle from snippet if available
                    match = re.search(r"\(@([\w\d_.-]+)\)", snippet)
                    if match:
                        return match.group(1)

                    # Final Backup: Extract from URL if valid
                    match = re.search(r"instagram\.com/([^/?]+)", link)
                    if match and "instagram.com/explore" not in link:
                        return match.group(1)

        except Exception as e:
            logging.error(f"Error fetching {query}: {e}")

        if attempt < retries:
            logging.info(f"Retrying {query} ({attempt + 1}/{retries})...")
            time.sleep(random.uniform(3, 7))  # Wait before retry

    return None


# Function to update Instagram handles in a batch
def update_instagram_handles_batch(handles):
    """
    Handles: List of tuples [(athlete_id, instagram_handle), ...]
    """
    cursor.executemany(
        "UPDATE athletes SET instagram_handle = %s WHERE athlete_id = %s", handles
    )
    conn.commit()


# Function to process a single athlete
def process_athlete(athlete):
    athlete_id, first_name, last_name, school_name = athlete
    handle = search_instagram_handle(first_name, last_name, school_name)

    if handle:
        return (handle, athlete_id)  # Store for batch update
    else:
        return None


# Main function (multi-threaded processing)
def main():
    while True:  # Keep running until all athletes are processed
        athletes = get_athletes(limit=50)  # Fetch 50 athletes at a time

        if not athletes:
            print("No more athletes to process.")
            break

        updates = []  # Store all results

        with ThreadPoolExecutor(max_workers=5) as executor:
            results = executor.map(process_athlete, athletes)

        for result in results:
            if result:
                updates.append(result)

        # Commit all updates at once (efficient)
        if updates:
            update_instagram_handles_batch(updates)
            print(f"Updated {len(updates)} athletes successfully.")

        # Sleep to avoid hitting API rate limits
        time.sleep(random.uniform(10, 20))


if __name__ == "__main__":
    try:
        main()
    finally:
        cursor.close()
        conn.close()
