"""
Neo4j knowledge graph schema definitions and initialization.
Defines nodes, relationships, constraints, and indexes for the medication advisor KG.
"""

from typing import List
from neo4j import GraphDatabase
from src.utils.config import config


class KnowledgeGraphSchema:
    """
    Knowledge Graph Schema for Medication Advisor.

    Nodes:
    - Patient: Represents a patient from discharge notes
    - Medication: Represents a drug/medication
    - Diagnosis: Represents a medical condition
    - Schedule: Represents dosing schedule (frequency, timing)
    - Interaction: Represents drug-drug interactions
    - Advice: Represents clinical advice/instructions

    Relationships:
    - (Patient)-[:HAS_DIAGNOSIS]->(Diagnosis)
    - (Patient)-[:TAKES]->(Medication)
    - (Medication)-[:HAS_SCHEDULE]->(Schedule)
    - (Medication)-[:INTERACTS_WITH]->(Medication)
    - (Medication)-[:CONTRAINDICATES]->(Diagnosis)
    - (Patient)-[:RECEIVED_ADVICE]->(Advice)
    - (Advice)-[:ABOUT_MEDICATION]->(Medication)
    """

    def __init__(self, uri: str = None, username: str = None, password: str = None):
        """Initialize connection to Neo4j."""
        self.uri = uri or config.NEO4J_URI
        self.username = username or config.NEO4J_USERNAME
        self.password = password or config.NEO4J_PASSWORD

        self.driver = GraphDatabase.driver(
            self.uri,
            auth=(self.username, self.password)
        )

    def close(self):
        """Close the database connection."""
        if self.driver:
            self.driver.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def verify_connection(self) -> bool:
        """Verify connection to Neo4j database."""
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                return result.single()["test"] == 1
        except Exception as e:
            print(f"Failed to connect to Neo4j: {e}")
            return False

    def initialize_schema(self):
        """Initialize the complete schema with constraints and indexes."""
        print("Initializing knowledge graph schema...")

        self.create_constraints()
        self.create_indexes()
        self.create_fulltext_indexes()

        print("Schema initialization complete!")

    def create_constraints(self):
        """Create uniqueness constraints for nodes."""
        constraints = [
            # Patient constraints
            "CREATE CONSTRAINT patient_id_unique IF NOT EXISTS FOR (p:Patient) REQUIRE p.patient_id IS UNIQUE",

            # Medication constraints
            "CREATE CONSTRAINT medication_name_unique IF NOT EXISTS FOR (m:Medication) REQUIRE m.name IS UNIQUE",

            # Diagnosis constraints
            "CREATE CONSTRAINT diagnosis_name_unique IF NOT EXISTS FOR (d:Diagnosis) REQUIRE d.name IS UNIQUE",

            # DrugBank ID constraint
            "CREATE CONSTRAINT drugbank_id_unique IF NOT EXISTS FOR (m:Medication) REQUIRE m.drugbank_id IS UNIQUE",
        ]

        with self.driver.session() as session:
            for constraint in constraints:
                try:
                    session.run(constraint)
                    print(f"Created constraint: {constraint[:50]}...")
                except Exception as e:
                    print(f"Constraint already exists or error: {e}")

    def create_indexes(self):
        """Create indexes for faster queries."""
        indexes = [
            # Medication indexes
            "CREATE INDEX medication_name_index IF NOT EXISTS FOR (m:Medication) ON (m.name)",

            # Diagnosis indexes
            "CREATE INDEX diagnosis_name_index IF NOT EXISTS FOR (d:Diagnosis) ON (d.name)",

            # Patient indexes
            "CREATE INDEX patient_id_index IF NOT EXISTS FOR (p:Patient) ON (p.patient_id)",

            # Schedule indexes
            "CREATE INDEX schedule_frequency_index IF NOT EXISTS FOR (s:Schedule) ON (s.frequency)",
        ]

        with self.driver.session() as session:
            for index in indexes:
                try:
                    session.run(index)
                    print(f"Created index: {index[:50]}...")
                except Exception as e:
                    print(f"Index already exists or error: {e}")

    def create_fulltext_indexes(self):
        """Create full-text search indexes for fuzzy matching."""
        fulltext_indexes = [
            # Medication full-text search
            """
            CREATE FULLTEXT INDEX medication_fulltext IF NOT EXISTS
            FOR (m:Medication) ON EACH [m.name, m.description]
            """,

            # Diagnosis full-text search
            """
            CREATE FULLTEXT INDEX diagnosis_fulltext IF NOT EXISTS
            FOR (d:Diagnosis) ON EACH [d.name]
            """,

            # Advice full-text search
            """
            CREATE FULLTEXT INDEX advice_fulltext IF NOT EXISTS
            FOR (a:Advice) ON EACH [a.text, a.category]
            """,
        ]

        with self.driver.session() as session:
            for index in fulltext_indexes:
                try:
                    session.run(index)
                    print(f"Created fulltext index")
                except Exception as e:
                    print(f"Fulltext index already exists or error: {e}")

    def clear_database(self, confirm: bool = False):
        """
        Clear all nodes and relationships from the database.
        WARNING: This will delete all data!
        """
        if not confirm:
            print("WARNING: This will delete all data from the database!")
            print("Call clear_database(confirm=True) to proceed.")
            return

        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            print("Database cleared!")

    def get_database_stats(self) -> dict:
        """Get statistics about the current database."""
        stats_query = """
        MATCH (n)
        WITH labels(n) as labels
        UNWIND labels as label
        RETURN label, count(*) as count
        ORDER BY count DESC
        """

        with self.driver.session() as session:
            result = session.run(stats_query)
            stats = {record["label"]: record["count"] for record in result}

        rel_query = """
        MATCH ()-[r]->()
        WITH type(r) as rel_type
        RETURN rel_type, count(*) as count
        ORDER BY count DESC
        """

        with self.driver.session() as session:
            result = session.run(rel_query)
            rel_stats = {record["rel_type"]: record["count"] for record in result}

        return {
            "nodes": stats,
            "relationships": rel_stats
        }

    def print_database_stats(self):
        """Print database statistics in a readable format."""
        stats = self.get_database_stats()

        print("\n" + "=" * 60)
        print("Knowledge Graph Statistics")
        print("=" * 60)

        print("\nNodes:")
        total_nodes = 0
        for label, count in stats["nodes"].items():
            print(f"  {label}: {count}")
            total_nodes += count
        print(f"  Total: {total_nodes}")

        print("\nRelationships:")
        total_rels = 0
        for rel_type, count in stats["relationships"].items():
            print(f"  {rel_type}: {count}")
            total_rels += count
        print(f"  Total: {total_rels}")

        print("=" * 60 + "\n")

    def get_sample_data(self, limit: int = 5) -> List[dict]:
        """Get sample nodes from the database."""
        query = f"""
        MATCH (n)
        RETURN labels(n)[0] as label, properties(n) as properties
        LIMIT {limit}
        """

        with self.driver.session() as session:
            result = session.run(query)
            return [{"label": record["label"], "properties": record["properties"]}
                    for record in result]

    def visualize_schema(self) -> str:
        """Generate a text representation of the schema."""
        schema_text = """
Knowledge Graph Schema:

Nodes:
  - Patient: patient_id, admission_date, discharge_date
  - Medication: name, drugbank_id, dosage, route, description
  - Diagnosis: name, code
  - Schedule: frequency, timing, instructions
  - Interaction: severity, description
  - Advice: text, category

Relationships:
  - (Patient)-[:HAS_DIAGNOSIS]->(Diagnosis)
  - (Patient)-[:TAKES {start_date, end_date}]->(Medication)
  - (Medication)-[:HAS_SCHEDULE]->(Schedule)
  - (Medication)-[:INTERACTS_WITH {severity}]->(Medication)
  - (Medication)-[:CONTRAINDICATES]->(Diagnosis)
  - (Patient)-[:RECEIVED_ADVICE]->(Advice)
  - (Advice)-[:ABOUT_MEDICATION]->(Medication)
  - (Medication)-[:DRUGBANK_INFO]->(DrugBankInfo)
        """
        return schema_text


def main():
    """Test schema initialization."""
    print("Testing Knowledge Graph Schema...")

    try:
        with KnowledgeGraphSchema() as kg:
            if not kg.verify_connection():
                print("Failed to connect to Neo4j!")
                print("Please check your Neo4j configuration in .env file")
                return

            print("Successfully connected to Neo4j!")

            choice = input("\nInitialize schema? (y/n): ").strip().lower()
            if choice == 'y':
                kg.initialize_schema()
                print("\nSchema initialized successfully!")

            print(kg.visualize_schema())

            if kg.get_database_stats()["nodes"]:
                kg.print_database_stats()

    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure Neo4j is running and credentials are correct.")


if __name__ == "__main__":
    main()
