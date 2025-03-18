from flask import Flask, request, jsonify, render_template, send_from_directory
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
from flask_cors import CORS

# Load environment variables (add this for better security)
load_dotenv()

app = Flask(__name__)
CORS(app)  # Add this line

# Neo4j Connection
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7689")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "fleish00")  # Fallback to hardcoded for now


class Neo4jQuery:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    def close(self):
        self.driver.close()

    def find_matching_players(self, input_name):
        """Find multiple matching players based on input."""
        query = """
        MATCH (p:Player)
        WHERE toLower(p.first_name + ' ' + p.last_name) CONTAINS toLower($input_name)
           OR toLower(p.first_name) CONTAINS toLower($input_name)
           OR toLower(p.last_name) CONTAINS toLower($input_name)
        RETURN p.first_name AS first_name, p.last_name AS last_name
        ORDER BY p.first_name, p.last_name
        LIMIT 10;
        """
        with self.driver.session() as session:
            result = session.run(query, {"input_name": input_name})
            return [record.data() for record in result]

    def get_top_connections(self, first_name, last_name):
        """Get top 10 strongest connections."""
        query = """
        MATCH (p:Player)-[r]-(teammate:Player)
        WHERE p.first_name = $first_name AND p.last_name = $last_name
        RETURN teammate.first_name AS teammate_first_name, 
               teammate.last_name AS teammate_last_name, 
               COUNT(r) AS connection_strength, 
               COLLECT(DISTINCT TYPE(r)) AS connection_types
        ORDER BY connection_strength DESC
        LIMIT 10;
        """
        with self.driver.session() as session:
            result = session.run(query, {"first_name": first_name, "last_name": last_name})
            connections = [record.data() for record in result]

            # Add ESPN profile URLs for each connection
            for conn in connections:
                first = conn["teammate_first_name"]
                last = conn["teammate_last_name"]
                # Create URL-friendly name format
                espn_name = f"{first.lower()}-{last.lower()}"
                # Generate ESPN profile URL
                conn[
                    "profile_url"] = f"https://www.espn.com/college-football/player/_/id/{self._generate_mock_id(first, last)}/{espn_name}"

            return connections

    def _generate_mock_id(self, first_name, last_name):
        """Generate a predictable mock ID based on player name.
        For demo purposes only - in production you'd use actual ESPN IDs."""
        # Generate a mock ESPN ID based on name
        return abs(hash(f"{first_name}{last_name}")) % 10000000


neo4j_query = Neo4jQuery()


# Add static file handler
@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/search_players', methods=['GET'])
def search_players():
    """Return a list of matching players for dropdown selection."""
    input_name = request.args.get("name")

    matches = neo4j_query.find_matching_players(input_name)
    if not matches:
        return jsonify([])  # Return an empty list if no players are found

    return jsonify(matches)


@app.route('/get_player_connections', methods=['POST'])
def get_player_connections():
    """Get top connections for the selected player."""
    selected_name = request.form.get("name")
    if not selected_name:
        return jsonify({"error": "No player selected"}), 400

    first_name, last_name = selected_name.split(" ", 1)  # Split into first and last name

    # Get top 10 strongest connections
    connections = neo4j_query.get_top_connections(first_name, last_name)

    # Calculate warm lead scores for each connection
    for conn in connections:
        # Base score is connection strength
        base_score = conn["connection_strength"]
        # Add bonus for certain connection types (PLAYED_WITH is stronger)
        type_bonus = 3 if "TEAMMATE_WITH" in conn["connection_types"] else 0
        # Calculate final score
        conn["warm_lead_score"] = base_score + type_bonus

    # Add ESPN profile URL for the main player
    espn_name = f"{first_name.lower()}-{last_name.lower()}"
    main_player_id = neo4j_query._generate_mock_id(first_name, last_name)
    main_player_url = f"https://www.espn.com/college-football/player/_/id/{main_player_id}/{espn_name}"

    return jsonify({
        "player": f"{first_name} {last_name}",
        "player_url": main_player_url,
        "top_connections": connections
    })


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    app.run(host='0.0.0.0', port=port)