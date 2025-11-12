"""
Load DrugBank data and create indexes in Neo4j
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from dotenv import load_dotenv
load_dotenv()

from src.etl.loaders import Neo4jLoader
from src.kg.schema import KnowledgeGraphSchema

print("=" * 60)
print("Neo4j Data Loader - DrugBank")
print("=" * 60)
print()

# Check if DrugBank data exists
drugbank_file = Path("src/data/drugbank/drugbank_clean.csv")

if not drugbank_file.exists():
    print(f"ERROR: DrugBank file not found: {drugbank_file}")
    print("Please ensure the data file exists.")
    sys.exit(1)

print(f"Found DrugBank data: {drugbank_file}")
print()

# Initialize loader
print("Connecting to Neo4j...")
with Neo4jLoader() as loader:
    if not loader.kg.verify_connection():
        print("ERROR: Cannot connect to Neo4j!")
        print("Check your .env file configuration.")
        sys.exit(1)

    print("Connected to Neo4j")
    print()

    # Load DrugBank data
    print("=" * 60)
    print("Loading DrugBank Medications")
    print("=" * 60)
    print()

    drugs_loaded = loader.load_drugbank_from_file(drugbank_file)

    print()
    print(f"Loaded {drugs_loaded} medications")
    print()

    # Create fulltext indexes
    print("=" * 60)
    print("Creating Fulltext Indexes")
    print("=" * 60)
    print()

    kg = loader.kg

    # Create medication fulltext index
    try:
        with kg.driver.session() as session:
            # Drop existing index if it exists
            try:
                session.run("DROP INDEX medication_fulltext IF EXISTS")
            except:
                pass

            # Create new index
            session.run("""
            CREATE FULLTEXT INDEX medication_fulltext IF NOT EXISTS
            FOR (m:Medication)
            ON EACH [m.name, m.description, m.indication]
            """)
            print("Created medication_fulltext index")
    except Exception as e:
        print(f"Note: Index creation - {str(e)[:100]}")

    # Create advice fulltext index (for future use)
    try:
        with kg.driver.session() as session:
            try:
                session.run("DROP INDEX advice_fulltext IF EXISTS")
            except:
                pass

            session.run("""
            CREATE FULLTEXT INDEX advice_fulltext IF NOT EXISTS
            FOR (a:Advice)
            ON EACH [a.text, a.category, a.details]
            """)
            print("Created advice_fulltext index")
    except Exception as e:
        print(f"Note: Advice index - {str(e)[:100]}")

    print()
    print("=" * 60)
    print("Data Loading Complete!")
    print("=" * 60)
    print()

    # Print stats
    kg.print_database_stats()

print()
print("All done! You can now run the demo.")
print()
