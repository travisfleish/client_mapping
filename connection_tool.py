from flask import Flask, request, jsonify, render_template
from neo4j import GraphDatabase

app = Flask(__name__)

# Neo4j Connection
NEO4J_URI = "bolt://localhost:7689"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "fleish00"


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
        RETURN p.first_name, p.last_name
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
        RETURN teammate.first_name, teammate.last_name, 
               COUNT(r) AS connection_strength, 
               COLLECT(DISTINCT TYPE(r)) AS connection_types
        ORDER BY connection_strength DESC
        LIMIT 10;
        """
        with self.driver.session() as session:
            result = session.run(query, {"first_name": first_name, "last_name": last_name})
            return [record.data() for record in result]


neo4j_query = Neo4jQuery()


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

    return jsonify({
        "player": f"{first_name} {last_name}",
        "top_connections": connections
    })


if __name__ == '__main__':
    app.run(debug=True)
