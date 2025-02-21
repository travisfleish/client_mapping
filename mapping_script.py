from neo4j import GraphDatabase
import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# PostgreSQL Connection
PG_DB_PARAMS = {
    "dbname": "sports_agency",
    "user": "postgres",
    "password": "fleish00",  # Change this if needed
    "host": "localhost",
    "port": "5432"
}

# Neo4j Connection
NEO4J_URI = "bolt://localhost:7689"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "fleish00"


class Neo4jLoader:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    def close(self):
        self.driver.close()

    def insert_data(self, query, params={}):
        """Run a Cypher query in Neo4j."""
        with self.driver.session() as session:
            session.run(query, params)


def fetch_roster_data():
    """Fetch complete roster data from PostgreSQL."""
    conn = psycopg2.connect(**PG_DB_PARAMS)
    cur = conn.cursor()

    cur.execute("""
        SELECT r.year, a.first_name, a.last_name, a.home_city, a.home_state, a.position, 
               t.team_id, t.name AS team_name
        FROM rosters r
        JOIN athletes a ON r.athlete_id = a.athlete_id
        JOIN teams t ON r.team_id = t.team_id
    """)

    data = cur.fetchall()
    cur.close()
    conn.close()
    return data


def load_data_into_neo4j():
    """Load fresh roster data from PostgreSQL into Neo4j."""
    neo4j_loader = Neo4jLoader()
    roster_data = fetch_roster_data()

    for row in roster_data:
        year, first_name, last_name, home_city, home_state, position, team_id, team_name = row

        # Handle NULL values by replacing them with "Unknown"
        home_city = home_city if home_city else "Unknown City"
        home_state = home_state if home_state else "Unknown State"
        position = position if position else "Unknown Position"
        first_name = first_name if first_name else "Unknown First Name"
        last_name = last_name if last_name else "Unknown Last Name"

        # ✅ Ensure Players with the Same Name Are Merged into One Node
        neo4j_loader.insert_data("""
            MERGE (p:Player {first_name: $first_name, last_name: $last_name})
            ON CREATE SET p.home_city = $home_city, p.home_state = $home_state, 
                          p.position = $position;
        """, {
            "first_name": first_name, "last_name": last_name,
            "home_city": home_city, "home_state": home_state, "position": position
        })

        # ✅ Ensure Team_Season Nodes Are Created (One Node per Team per Season)
        neo4j_loader.insert_data("""
            MERGE (ts:Team_Season {team_id: $team_id, year: $year})
            ON CREATE SET ts.name = $team_name + " " + $year;
        """, {"team_id": team_id, "team_name": team_name, "year": year})

        # ✅ Link Player to Team_Season (PLAYED_FOR)
        neo4j_loader.insert_data("""
            MATCH (p:Player {first_name: $first_name, last_name: $last_name}),
                  (ts:Team_Season {team_id: $team_id, year: $year})
            MERGE (p)-[:PLAYED_FOR]->(ts);
        """, {"first_name": first_name, "last_name": last_name, "team_id": team_id, "year": year})

    neo4j_loader.close()
    print("✅ Neo4j database successfully reset and populated!")


if __name__ == "__main__":
    load_data_into_neo4j()
