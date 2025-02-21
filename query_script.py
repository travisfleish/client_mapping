import openai
import psycopg2
import os
from dotenv import load_dotenv

# Load API key from .env
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Database connection settings
DB_PARAMS = {
    "dbname": "sports_agency",
    "user": "postgres",
    "password": "fleish00",  # Change this to your actual password
    "host": "localhost",
    "port": "5432"
}

def get_sql_query_from_openai(prompt):
    """Send a natural language prompt to OpenAI and receive a well-formed SQL query."""
    client = openai.OpenAI()

    system_message = """
    You are an expert in sports analytics and SQL query generation. You will be given a natural language question
    and must return **only the SQL query**, formatted correctly for PostgreSQL.

    ### Database Schema:
    - `athletes` (athlete_id, first_name, last_name, home_city, home_state, position)
    - `teams` (team_id, name)
    - `rosters` (roster_id, athlete_id, team_id, year)

    ### Special Instructions:
    1. **Correct typos** in team names (e.g., "Auburm" → "Auburn").
    2. **Use position abbreviations** (e.g., "wide receiver" → "WR").
    3. **Ensure queries are optimized** (e.g., JOINs instead of subqueries when possible).
    4. **Return only the SQL query**, without explanations, markdown formatting, or assumptions.

    Example Input: "What wide receivers did Bo Nix play with at Auburm?"
    Example Output:
    SELECT a.first_name, a.last_name
    FROM athletes a
    JOIN rosters r ON a.athlete_id = r.athlete_id 
    JOIN teams t ON r.team_id = t.team_id
    WHERE a.position = 'WR'
    AND t.name = 'Auburn'
    AND r.year IN (
        SELECT r2.year 
        FROM rosters r2 
        JOIN athletes a2 ON r2.athlete_id = a2.athlete_id 
        WHERE a2.first_name = 'Bo' 
        AND a2.last_name = 'Nix'
    );
    """

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"Convert this into an SQL query: {prompt}"}
        ]
    )

    sql_query = response.choices[0].message.content.strip()

    # Extract only the SQL query (in case OpenAI adds extra formatting)
    if "```sql" in sql_query:
        sql_query = sql_query.split("```sql")[1].split("```")[0].strip()

    return sql_query

def execute_sql_query(query):
    """Execute the generated SQL query and return the results."""
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        cur.execute(query)
        results = cur.fetchall()
        cur.close()
        conn.close()
        return results
    except Exception as e:
        return f"Error executing query: {e}"

def main():
    """Main function to take user input, generate SQL, and execute the query."""
    print("🔍 Enter your question (or type 'exit' to quit):")
    while True:
        user_prompt = input("> ")

        if user_prompt.lower() == "exit":
            print("Goodbye! 👋")
            break

        print("\n🧠 Generating SQL query...")
        sql_query = get_sql_query_from_openai(user_prompt)
        print(f"\n📝 Generated SQL Query:\n{sql_query}\n")

        print("🔄 Executing query...")
        results = execute_sql_query(sql_query)

        print("\n📊 Query Results:")
        for row in results:
            print(row)

if __name__ == "__main__":
    main()
