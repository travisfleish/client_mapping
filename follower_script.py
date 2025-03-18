from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import os
import psycopg2
import csv

# PostgreSQL connection
conn = psycopg2.connect(
    dbname="sports_agency",
    user="postgres",
    password="fleish00",  # Change if needed
    host="localhost",
    port="5432"
)
cursor = conn.cursor()

# Set up Selenium WebDriver
options = webdriver.ChromeOptions()
options.add_argument("user-data-dir=chrome-data")  # Keeps session logged in
driver = webdriver.Chrome(options=options)

def trigger_ig_export(instagram_handle, athlete_id):
    """Triggers IG Export without opening Instagram."""

    # **Open a blank page (or any site) instead of Instagram**
    driver.get("about:blank")
    time.sleep(2)

    # **Trigger IG Follower Export using keyboard shortcut (default: ALT+SHIFT+E)**
    webdriver.ActionChains(driver).key_down(Keys.ALT).send_keys(Keys.SHIFT, 'E').key_up(Keys.ALT).perform()

    print(f"Triggered IG Export for {instagram_handle}. Waiting for file download...")
    time.sleep(30)  # Wait for the export to finish

    # **Process CSV after export**
    process_csv(instagram_handle, athlete_id)

def process_csv(instagram_handle, athlete_id):
    """Reads the exported CSV and inserts following data into PostgreSQL."""
    downloads_path = "/Users/travisfleisher/Downloads"  # Adjust path as needed
    csv_filename = f"{downloads_path}/{instagram_handle}_following.csv"

    if not os.path.exists(csv_filename):
        print(f"CSV file not found: {csv_filename}")
        return

    with open(csv_filename, newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)

        if "userName" not in reader.fieldnames:
            print("Error: 'userName' column not found in CSV.")
            return

        for row in reader:
            followed_user = row["userName"].strip()  # Extract correct username

            cursor.execute("""
                INSERT INTO followers (athlete_id, instagram_handle, follows)
                VALUES (%s, %s, %s) ON CONFLICT DO NOTHING;
            """, (athlete_id, instagram_handle, followed_user))

    conn.commit()
    print(f"Inserted following list for {instagram_handle} into PostgreSQL.")

# **Example Usage**
trigger_ig_export("flyguy_ea", 3116577)

driver.quit()
cursor.close()
conn.close()
