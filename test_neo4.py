from neo4j import GraphDatabase

# Neo4j Connection Details
NEO4J_URI = "bolt://localhost:7689"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "fleish00"

class Neo4jTester:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    def close(self):
        self.driver.close()

    def test_connection(self):
        """Test basic Neo4j connection."""
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 'Neo4j Connection Successful' AS message")
                print(result.single()["message"])
        except Exception as e:
            print("Neo4j Connection Failed:", e)

    def check_bo_nix(self):
        """Check if Bo Nix exists in the database."""
        query = """
        MATCH (p:Player)
        WHERE p.first_name = 'Bo' AND p.last_name = 'Nix'
        RETURN p.first_name, p.last_name
        """
        with self.driver.session() as session:
            result = session.run(query)
            record = result.single()
            if record:
                print(f"✅ Found player: {record['p.first_name']} {record['p.last_name']}")
            else:
                print("❌ Bo Nix not found in Neo4j.")

# Run Tests
neo4j_tester = Neo4jTester()
neo4j_tester.test_connection()  # Test connection
neo4j_tester.check_bo_nix()  # Test Bo Nix exists
neo4j_tester.close()
