"""
Cypher query builders for knowledge graph retrieval.
Dynamic query generation based on input parameters.
"""

from typing import List, Dict, Optional, Any
from langchain_community.vectorstores.neo4j_vector import remove_lucene_chars


class MedicationQueryBuilder:
    """Build Cypher queries for medication-related information."""

    @staticmethod
    def find_medication_by_name(medication_name: str, limit: int = 3) -> tuple[str, dict]:
        """
        Build query to find medications by name using fulltext search.

        Returns:
            Tuple of (query_string, parameters_dict)
        """
        ft_query = generate_full_text_query(medication_name)

        query = """
        CALL db.index.fulltext.queryNodes('medication_fulltext', $fulltextQuery, {limit: $limit})
        YIELD node
        RETURN node.name AS name,
               node.drugbank_id AS drugbank_id,
               node.description AS description
        """

        params = {
            "fulltextQuery": ft_query,
            "limit": limit
        }

        return query, params

    @staticmethod
    def get_medication_schedule(
        medication_name: str,
        patient_id: Optional[str] = None
    ) -> tuple[str, dict]:
        """
        Build query to get medication schedule and dosing information.

        Args:
            medication_name: Name of the medication
            patient_id: Optional patient ID to get patient-specific schedule

        Returns:
            Tuple of (query_string, parameters_dict)
        """
        if patient_id:
            query = """
            MATCH (p:Patient {patient_id: $patient_id})-[:TAKES]->(m:Medication)
            WHERE m.name =~ $med_pattern
            OPTIONAL MATCH (m)-[:HAS_SCHEDULE]->(s:Schedule)
            RETURN m.name AS medication,
                   m.dosage AS dosage,
                   m.route AS route,
                   s.frequency AS frequency,
                   s.timing AS timing,
                   s.instructions AS instructions
            """
            params = {
                "patient_id": patient_id,
                "med_pattern": f"(?i).*{medication_name}.*"
            }
        else:
            query = """
            MATCH (m:Medication)
            WHERE m.name =~ $med_pattern
            OPTIONAL MATCH (m)-[:HAS_SCHEDULE]->(s:Schedule)
            RETURN m.name AS medication,
                   m.dosage AS dosage,
                   m.route AS route,
                   s.frequency AS frequency,
                   s.timing AS timing,
                   s.instructions AS instructions
            LIMIT 5
            """
            params = {
                "med_pattern": f"(?i).*{medication_name}.*"
            }

        return query, params

    @staticmethod
    def get_drug_interactions(medication_name: str) -> tuple[str, dict]:
        """
        Build query to find drug-drug interactions.

        Args:
            medication_name: Name of the medication to check

        Returns:
            Tuple of (query_string, parameters_dict)
        """
        query = """
        MATCH (m1:Medication)-[i:INTERACTS_WITH]-(m2:Medication)
        WHERE m1.name =~ $med_pattern
        RETURN m1.name AS medication,
               m2.name AS interacting_drug,
               i.severity AS severity,
               i.description AS description
        ORDER BY
            CASE i.severity
                WHEN 'severe' THEN 1
                WHEN 'moderate' THEN 2
                WHEN 'mild' THEN 3
                ELSE 4
            END
        LIMIT 10
        """

        params = {
            "med_pattern": f"(?i).*{medication_name}.*"
        }

        return query, params

    @staticmethod
    def get_contraindications(
        medication_name: Optional[str] = None,
        diagnosis: Optional[str] = None
    ) -> tuple[str, dict]:
        """
        Build query to find contraindications between medications and diagnoses.

        Args:
            medication_name: Name of medication (optional)
            diagnosis: Name of diagnosis (optional)

        Returns:
            Tuple of (query_string, parameters_dict)
        """
        where_clauses = []
        params = {}

        if medication_name:
            where_clauses.append("m.name =~ $med_pattern")
            params["med_pattern"] = f"(?i).*{medication_name}.*"

        if diagnosis:
            where_clauses.append("d.name =~ $diag_pattern")
            params["diag_pattern"] = f"(?i).*{diagnosis}.*"

        where_clause = " AND ".join(where_clauses) if where_clauses else "true"

        query = f"""
        MATCH (m:Medication)-[c:CONTRAINDICATES]->(d:Diagnosis)
        WHERE {where_clause}
        RETURN m.name AS medication,
               d.name AS diagnosis,
               c.severity AS severity,
               c.reason AS reason
        LIMIT 10
        """

        return query, params


class PatientQueryBuilder:
    """Build Cypher queries for patient-related information."""

    @staticmethod
    def get_patient_medications(patient_id: str) -> tuple[str, dict]:
        """Get all medications for a specific patient."""
        query = """
        MATCH (p:Patient {patient_id: $patient_id})-[t:TAKES]->(m:Medication)
        OPTIONAL MATCH (m)-[:HAS_SCHEDULE]->(s:Schedule)
        RETURN p.patient_id AS patient_id,
               m.name AS medication,
               m.dosage AS dosage,
               m.route AS route,
               s.frequency AS frequency,
               s.instructions AS instructions,
               t.start_date AS start_date,
               t.end_date AS end_date
        ORDER BY m.name
        """

        params = {"patient_id": patient_id}
        return query, params

    @staticmethod
    def get_patient_diagnoses(patient_id: str) -> tuple[str, dict]:
        """Get all diagnoses for a specific patient."""
        query = """
        MATCH (p:Patient {patient_id: $patient_id})-[:HAS_DIAGNOSIS]->(d:Diagnosis)
        RETURN p.patient_id AS patient_id,
               d.name AS diagnosis,
               d.code AS diagnosis_code
        ORDER BY d.name
        """

        params = {"patient_id": patient_id}
        return query, params

    @staticmethod
    def get_patient_advice(
        patient_id: str,
        category: Optional[str] = None
    ) -> tuple[str, dict]:
        """Get discharge advice for a patient, optionally filtered by category."""
        where_clause = ""
        params = {"patient_id": patient_id}

        if category:
            where_clause = "AND a.category = $category"
            params["category"] = category

        query = f"""
        MATCH (p:Patient {{patient_id: $patient_id}})-[:RECEIVED_ADVICE]->(a:Advice)
        {where_clause}
        OPTIONAL MATCH (a)-[:ABOUT_MEDICATION]->(m:Medication)
        RETURN a.text AS advice,
               a.category AS category,
               collect(m.name) AS related_medications
        ORDER BY a.category
        """

        return query, params


class AdviceQueryBuilder:
    """Build queries for medication advice and instructions."""

    @staticmethod
    def search_advice(
        search_term: str,
        medication_name: Optional[str] = None,
        limit: int = 5
    ) -> tuple[str, dict]:
        """Search for advice using fulltext search."""
        ft_query = generate_full_text_query(search_term)
        params = {
            "fulltextQuery": ft_query,
            "limit": limit
        }

        if medication_name:
            query = """
            CALL db.index.fulltext.queryNodes('advice_fulltext', $fulltextQuery, {limit: $limit})
            YIELD node
            MATCH (node)-[:ABOUT_MEDICATION]->(m:Medication)
            WHERE m.name =~ $med_pattern
            RETURN node.text AS advice,
                   node.category AS category,
                   m.name AS medication
            """
            params["med_pattern"] = f"(?i).*{medication_name}.*"
        else:
            query = """
            CALL db.index.fulltext.queryNodes('advice_fulltext', $fulltextQuery, {limit: $limit})
            YIELD node
            OPTIONAL MATCH (node)-[:ABOUT_MEDICATION]->(m:Medication)
            RETURN node.text AS advice,
                   node.category AS category,
                   collect(m.name) AS medications
            """

        return query, params


class DrugInfoQueryBuilder:
    """Build queries for DrugBank information."""

    @staticmethod
    def get_drug_info(medication_name: str) -> tuple[str, dict]:
        """Get detailed drug information from DrugBank."""
        query = """
        MATCH (m:Medication)
        WHERE m.name =~ $med_pattern
        RETURN m.name AS medication,
               m.drugbank_id AS drugbank_id,
               m.description AS description,
               m.indication AS indication,
               m.mechanism AS mechanism,
               m.pharmacodynamics AS pharmacodynamics,
               m.metabolism AS metabolism,
               m.toxicity AS toxicity
        LIMIT 1
        """

        params = {
            "med_pattern": f"(?i).*{medication_name}.*"
        }

        return query, params


def generate_full_text_query(input_str: str) -> str:
    """
    Generate a full-text search query for a given input string.

    This function constructs a query string suitable for a full-text search.
    It processes the input string by splitting it into words and appending a
    similarity threshold (~2) to each word, then combines them using the AND
    operator. Useful for mapping medications from user questions to database
    values, and allows for some misspellings.

    Args:
        input_str: The search input string

    Returns:
        Formatted fulltext query string
    """
    full_text_query = ""
    words = [el for el in remove_lucene_chars(input_str).split() if el]

    if not words:
        return ""

    for word in words[:-1]:
        full_text_query += f" {word}~2 AND"
    full_text_query += f" {words[-1]}~2"

    return full_text_query.strip()


def execute_query(driver, query: str, params: Dict[str, Any]) -> List[Dict]:
    """
    Execute a Cypher query and return results.

    Args:
        driver: Neo4j driver instance
        query: Cypher query string
        params: Query parameters

    Returns:
        List of result dictionaries
    """
    with driver.session() as session:
        result = session.run(query, params)
        return [dict(record) for record in result]


if __name__ == "__main__":
    print("Testing query builders...")

    # Test medication query
    query, params = MedicationQueryBuilder.get_medication_schedule("metformin")
    print("\nMedication Schedule Query:")
    print(query)
    print("Parameters:", params)

    # Test interaction query
    query, params = MedicationQueryBuilder.get_drug_interactions("warfarin")
    print("\nDrug Interactions Query:")
    print(query)
    print("Parameters:", params)

    # Test fulltext query generation
    ft_query = generate_full_text_query("metformin hydrochloride")
    print("\nFulltext Query:")
    print(ft_query)
