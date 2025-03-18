import psycopg2
import pandas as pd

# PostgreSQL connection
conn = psycopg2.connect(
    dbname="sports_agency",
    user="postgres",
    password="fleish00",
    host="localhost",
    port="5432"
)

# SQL Query to get only one entry per athlete (most recent school attended)
query = """
    SELECT DISTINCT ON (a.athlete_id) 
        a.athlete_id, a.first_name, a.last_name, t.name AS school_name
    FROM athletes a
    JOIN rosters r ON a.athlete_id = r.athlete_id
    JOIN teams t ON r.team_id = t.team_id
    ORDER BY a.athlete_id, r.year DESC;
"""

# Load data into Pandas DataFrame
df = pd.read_sql(query, conn)

# Add a column with row numbers starting from 1
df.insert(0, 'row_number', range(1, len(df) + 1))

# Export to CSV
df.to_csv("/Users/travisfleisher/Downloads/players.csv", index=False)

print("CSV export complete!")

# Close connection
conn.close()