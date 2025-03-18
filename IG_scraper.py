import psycopg2
import time
import os
import random
import re
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
SERPAPI_KEY = "a273feac892ece4ea8bfac234ae8ad47c04a557813654e514cc2e0e429cdc868"


# Function to fetch athletes from database
def get_athletes(limit=100):
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


# Function to search Instagram profiles using SerpAPI
def search_instagram_handle(first_name, last_name, school_name):
    # Use school name in the query
    query = f"{first_name} {last_name} {school_name} Instagram"
    params = {
        "engine": "google",
        "q": query,
        "api_key": SERPAPI_KEY
    }

    search = GoogleSearch(params)
    results = search.get_dict()

    # Debugging: Print raw API response
    print(f"Search results for {first_name} {last_name}: {results}")

    if "organic_results" in results:
        for result in results["organic_results"]:
            title = result.get("title", "")
            snippet = result.get("snippet", "")
            link = result.get("link", "")

            # Ignore results from Instagram Explore, Locations, or Non-Personal Accounts
            if "/explore/" in link or "/locations/" in link:
                continue

            # Extract handle from title text (@username)
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

    return None


# Function to update Instagram handles in PostgreSQL
def update_instagram_handle(athlete_id, handle):
    cursor.execute("UPDATE athletes SET instagram_handle = %s WHERE athlete_id = %s", (handle, athlete_id))
    conn.commit()


# Main function
def main():
    athletes = get_athletes(limit=50)  # Fetch 50 athletes at a time
    for athlete in athletes:
        athlete_id, first_name, last_name, school_name = athlete
        handle = search_instagram_handle(first_name, last_name, school_name)
        if handle:
            update_instagram_handle(athlete_id, handle)
            print(f"Updated: {first_name} {last_name} -> @{handle}")
        else:
            print(f"No Instagram found for {first_name} {last_name}")

        time.sleep(random.uniform(3, 7))  # Reduce request frequency to stay under API limits


if __name__ == "__main__":
    main()
    cursor.close()
    conn.close()
