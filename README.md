# Sports Agency Client Mapping Tool

## Overview
The **Sports Agency Client Mapping Tool** is designed to provide a **competitive advantage in recruiting** by mapping relationships between **athletes, teams, agents, and endorsements**. The system identifies **"warm leads"** based on shared history, social media engagement, and professional connections.

## Features
- **Automated Data Collection**: Pulls NFL and Power 5 college football roster data via APIs/web scraping.
- **Relationship Mapping**: Uses **Neo4j** to track teammates, transfers, NIL deals, and agency ties.
- **Database Integration**: Stores structured data in **PostgreSQL** for easy querying.
- **Warm Lead Scoring Algorithm**: Evaluates player connections and ranks recruiting opportunities.
- **Searchable Dashboard (Future Feature)**: Allows agents to find top player connections dynamically.

## Tech Stack
- **Programming Language**: Python
- **Databases**: PostgreSQL (structured data), Neo4j (graph relationships)
- **APIs & Scraping**: Requests, BeautifulSoup
- **Version Control**: Git & GitHub

## Project Structure
```
├── data/                  # Stores raw & cleaned data
│   ├── raw/               # Unprocessed data
│   ├── cleaned/           # Cleaned, structured data
├── scripts/               # Python scripts for automation
│   ├── collect_data.py    # Automates data collection
│   ├── process_data.py    # Cleans & structures data
│   ├── load_data.py       # Loads data into PostgreSQL & Neo4j
├── db/                    # Database setup & queries
│   ├── neo4j_setup.cypher # Neo4j schema & constraints
│   ├── postgres_setup.sql # PostgreSQL table setup
├── notebooks/             # Jupyter notebooks for analysis
├── config/                # Configuration files (DO NOT COMMIT credentials)
│   ├── settings.py        # Stores database/API credentials
├── .gitignore             # Excludes sensitive files
├── README.md              # Project overview (this file)
├── requirements.txt       # List of dependencies
```

## Installation & Setup
### **1️⃣ Clone the Repository**
```bash
git clone https://github.com/travisfleish/client_mapping.git
cd client_mapping
```
### **2️⃣ Set Up a Virtual Environment**
```bash
python -m venv .venv
source .venv/bin/activate  # On Mac/Linux
.venv\Scripts\activate    # On Windows
```
### **3️⃣ Install Dependencies**
```bash
pip install -r requirements.txt
```
### **4️⃣ Set Up Databases**
Ensure **PostgreSQL and Neo4j** are installed and running:
```bash
# PostgreSQL: Run setup script
psql -U admin -d sports_agency -f db/postgres_setup.sql

# Neo4j: Open Browser & Run Cypher Script
cat db/neo4j_setup.cypher | cypher-shell -u neo4j -p password
```

## Usage
### **Running Data Collection**
```bash
python scripts/collect_data.py
```
### **Processing & Loading Data**
```bash
python scripts/process_data.py
python scripts/load_data.py
```
### **Running Queries in Neo4j**
```cypher
MATCH (a:Athlete)-[:PLAYED_WITH]->(b:Athlete)
WHERE a.name = "Sauce Gardner"
RETURN b.name;
```

## Contributing
- Fork the repository & create a new branch
- Commit changes with meaningful messages
- Push and create a PR for review

## Future Enhancements
- Build a **web dashboard** for agents to search player connections.
- Expand data sources beyond Power 5 schools & NFL.
- Improve **warm lead scoring algorithm** with AI-powered predictions.

## License
MIT License

---
📩 **Need Help?** Contact `travisfleish` on GitHub!

