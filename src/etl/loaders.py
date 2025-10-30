"""
Data loaders for inserting graph entities into Neo4j.
Handles batch loading, deduplication, and relationship creation.
"""

from typing import List, Dict
from pathlib import Path
from tqdm import tqdm

from src.kg.schema import KnowledgeGraphSchema
from src.etl.extractors import GraphNode, GraphRelationship, DischargeNoteExtractor, DrugBankExtractor
from src.data.parsers import DischargeNoteParser, DrugBankParser
from src.data.models import DischargeNote, DrugInfo


class Neo4jLoader:
    """Handles loading data into Neo4j knowledge graph."""

    def __init__(self, kg_schema: KnowledgeGraphSchema = None):
        """Initialize loader with Neo4j connection."""
        self.kg = kg_schema or KnowledgeGraphSchema()

    def close(self):
        """Close the database connection."""
        if self.kg:
            self.kg.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def load_node(self, node: GraphNode) -> bool:
        """
        Load a single node into Neo4j using MERGE (creates or updates).

        Args:
            node: GraphNode to load

        Returns:
            True if successful
        """
        properties_str = ', '.join([f"{k}: ${k}" for k in node.properties.keys()])

        merge_key = self._get_merge_key(node.label)
        if merge_key and merge_key in node.properties:
            query = f"""
            MERGE (n:{node.label} {{{merge_key}: ${merge_key}}})
            ON CREATE SET n = $properties
            ON MATCH SET n += $properties
            RETURN n
            """
        else:
            query = f"""
            CREATE (n:{node.label})
            SET n = $properties
            RETURN n
            """

        params = {**node.properties, 'properties': node.properties}

        try:
            with self.kg.driver.session() as session:
                session.run(query, params)
            return True
        except Exception as e:
            print(f"Error loading node {node.label}: {e}")
            return False

    def _get_merge_key(self, label: str) -> str:
        """Get the merge key for a node label."""
        merge_keys = {
            'Patient': 'patient_id',
            'Medication': 'name',
            'Diagnosis': 'name',
            'Schedule': None,  # Schedules don't have unique keys
            'Advice': None,
            'Interaction': None,
        }
        return merge_keys.get(label)

    def load_nodes_batch(self, nodes: List[GraphNode], batch_size: int = 100) -> int:
        """
        Load multiple nodes in batches.

        Args:
            nodes: List of GraphNodes
            batch_size: Number of nodes per batch

        Returns:
            Number of nodes loaded
        """
        loaded_count = 0

        for i in tqdm(range(0, len(nodes), batch_size), desc="Loading nodes"):
            batch = nodes[i:i + batch_size]

            for node in batch:
                if self.load_node(node):
                    loaded_count += 1

        return loaded_count

    def load_relationship(self, rel: GraphRelationship) -> bool:
        """
        Load a single relationship into Neo4j.

        Args:
            rel: GraphRelationship to load

        Returns:
            True if successful
        """
        from_key = self._get_merge_key(rel.from_node.label)
        to_key = self._get_merge_key(rel.to_node.label)

        if not from_key:
            from_match = f"MATCH (from:{rel.from_node.label})"
        else:
            from_match = f"MATCH (from:{rel.from_node.label} {{{from_key}: $from_{from_key}}})"

        if not to_key:
            to_match = f"MATCH (to:{rel.to_node.label})"
        else:
            to_match = f"MATCH (to:{rel.to_node.label} {{{to_key}: $to_{to_key}}})"

        if rel.properties:
            props_str = "{" + ', '.join([f"{k}: ${k}" for k in rel.properties.keys()]) + "}"
            rel_str = f"[r:{rel.rel_type} {props_str}]"
        else:
            rel_str = f"[r:{rel.rel_type}]"

        query = f"""
        {from_match}
        {to_match}
        MERGE (from)-{rel_str}->(to)
        RETURN r
        """

        params = {}

        if from_key:
            params[f"from_{from_key}"] = rel.from_node.properties[from_key]

        if to_key:
            params[f"to_{to_key}"] = rel.to_node.properties[to_key]

        if rel.properties:
            params.update(rel.properties)

        try:
            with self.kg.driver.session() as session:
                result = session.run(query, params)
                result.single()
            return True
        except Exception as e:
            print(f"Error loading relationship {rel.rel_type}: {e}")
            return False

    def load_relationships_batch(
        self,
        relationships: List[GraphRelationship],
        batch_size: int = 100
    ) -> int:
        """
        Load multiple relationships in batches.

        Args:
            relationships: List of GraphRelationships
            batch_size: Number of relationships per batch

        Returns:
            Number of relationships loaded
        """
        loaded_count = 0

        for i in tqdm(range(0, len(relationships), batch_size), desc="Loading relationships"):
            batch = relationships[i:i + batch_size]

            for rel in batch:
                if self.load_relationship(rel):
                    loaded_count += 1

        return loaded_count

    def load_discharge_note(self, note: DischargeNote) -> Dict[str, int]:
        """
        Load a complete discharge note into the knowledge graph.

        Args:
            note: Parsed DischargeNote

        Returns:
            Dictionary with counts of loaded entities
        """
        nodes, relationships = DischargeNoteExtractor.extract_all_entities(note)

        nodes_loaded = self.load_nodes_batch(nodes)
        rels_loaded = self.load_relationships_batch(relationships)

        return {
            'nodes': nodes_loaded,
            'relationships': rels_loaded
        }

    def load_discharge_notes_from_directory(
        self,
        directory: Path,
        limit: int = None
    ) -> Dict[str, int]:
        """
        Load all discharge notes from a directory.

        Args:
            directory: Path to directory containing .txt files
            limit: Optional limit on number of files to process

        Returns:
            Dictionary with total counts
        """
        txt_files = list(directory.glob("*.txt"))

        if limit:
            txt_files = txt_files[:limit]

        total_nodes = 0
        total_rels = 0

        print(f"Loading {len(txt_files)} discharge notes...")

        for file_path in tqdm(txt_files, desc="Processing files"):
            try:
                note = DischargeNoteParser.parse_file(file_path)
                counts = self.load_discharge_note(note)
                total_nodes += counts['nodes']
                total_rels += counts['relationships']
            except Exception as e:
                print(f"Error processing {file_path.name}: {e}")

        return {
            'total_files': len(txt_files),
            'total_nodes': total_nodes,
            'total_relationships': total_rels
        }

    def load_drugbank_data(self, drugs: List[DrugInfo]) -> int:
        """
        Load DrugBank medication data into the knowledge graph.

        Args:
            drugs: List of DrugInfo objects

        Returns:
            Number of drugs loaded
        """
        medication_nodes = DrugBankExtractor.extract_all_medications(drugs)

        print(f"Loading {len(medication_nodes)} medications from DrugBank...")
        return self.load_nodes_batch(medication_nodes)

    def load_drugbank_from_file(self, file_path: Path) -> int:
        """
        Load DrugBank data from a CSV/TSV file.

        Args:
            file_path: Path to DrugBank CSV/TSV file

        Returns:
            Number of drugs loaded
        """
        print(f"Parsing DrugBank file: {file_path}")
        drugs = DrugBankParser.parse_file(file_path)

        return self.load_drugbank_data(drugs)

    def enrich_medications_with_drugbank(self):
        """
        Enrich existing medications in the graph with DrugBank information.
        Matches medications by name and updates their properties.
        """
        query = """
        MATCH (m1:Medication)
        WHERE m1.drugbank_id IS NOT NULL
        MATCH (m2:Medication {name: m1.name})
        WHERE m2.drugbank_id IS NULL
        SET m2.drugbank_id = m1.drugbank_id,
            m2.description = m1.description,
            m2.indication = m1.indication,
            m2.mechanism = m1.mechanism,
            m2.pharmacodynamics = m1.pharmacodynamics,
            m2.metabolism = m1.metabolism,
            m2.toxicity = m1.toxicity
        RETURN count(m2) as enriched_count
        """

        with self.kg.driver.session() as session:
            result = session.run(query)
            count = result.single()["enriched_count"]
            print(f"Enriched {count} medications with DrugBank data")
            return count


def run_etl_pipeline(
    discharge_notes_dir: Path = None,
    drugbank_file: Path = None,
    limit_notes: int = None
):
    """
    Run the complete ETL pipeline to load data into Neo4j.

    Args:
        discharge_notes_dir: Directory containing discharge note .txt files
        drugbank_file: Path to DrugBank CSV/TSV file
        limit_notes: Optional limit on number of discharge notes to process
    """
    print("=" * 60)
    print("Starting ETL Pipeline")
    print("=" * 60)

    with Neo4jLoader() as loader:
        if not loader.kg.verify_connection():
            print("ERROR: Cannot connect to Neo4j!")
            print("Please check your Neo4j configuration and ensure it's running.")
            return

        print("\nNeo4j connection verified!")

        if drugbank_file and drugbank_file.exists():
            print("\n" + "=" * 60)
            print("Loading DrugBank Data")
            print("=" * 60)
            drugs_loaded = loader.load_drugbank_from_file(drugbank_file)
            print(f"Loaded {drugs_loaded} drugs from DrugBank")

        if discharge_notes_dir and discharge_notes_dir.exists():
            print("\n" + "=" * 60)
            print("Loading Discharge Notes")
            print("=" * 60)
            results = loader.load_discharge_notes_from_directory(
                discharge_notes_dir,
                limit=limit_notes
            )
            print(f"\nResults:")
            print(f"  Files processed: {results['total_files']}")
            print(f"  Nodes created: {results['total_nodes']}")
            print(f"  Relationships created: {results['total_relationships']}")

            if drugbank_file:
                print("\n" + "=" * 60)
                print("Enriching Medications with DrugBank Data")
                print("=" * 60)
                loader.enrich_medications_with_drugbank()

        print("\n" + "=" * 60)
        print("ETL Pipeline Complete!")
        print("=" * 60)

        loader.kg.print_database_stats()


if __name__ == "__main__":
    from src.utils.config import config

    print("Neo4j Data Loader")
    print("=" * 60)

    sample_dir = config.DATA_DIR / "samples"

    if sample_dir.exists():
        print(f"\nFound sample data directory: {sample_dir}")
        print("Running ETL pipeline on sample data...\n")

        run_etl_pipeline(
            discharge_notes_dir=sample_dir,
            drugbank_file=sample_dir / "sample_drugbank.csv"
        )
    else:
        print("\nNo sample data found.")
        print("Run src/data/downloaders.py to create sample data first.")
