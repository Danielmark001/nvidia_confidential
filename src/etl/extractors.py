"""
Data extractors for creating knowledge graph triples.
Converts parsed data into graph-ready format (nodes and relationships).
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

from src.data.models import DischargeNote, Medication, DrugInfo


@dataclass
class GraphNode:
    """Represents a node in the knowledge graph."""
    label: str  # Node type (Patient, Medication, etc.)
    properties: Dict  # Node properties


@dataclass
class GraphRelationship:
    """Represents a relationship in the knowledge graph."""
    from_node: GraphNode
    rel_type: str  # Relationship type
    to_node: GraphNode
    properties: Dict = None  # Optional relationship properties

    def __post_init__(self):
        if self.properties is None:
            self.properties = {}


class DischargeNoteExtractor:
    """Extract graph entities from discharge notes."""

    @staticmethod
    def extract_patient_node(note: DischargeNote) -> GraphNode:
        """Extract patient node from discharge note."""
        patient_id = note.patient_id or f"patient_{hash(note.raw_text[:100]) % 10000}"

        return GraphNode(
            label="Patient",
            properties={
                "patient_id": patient_id,
                "admission_date": note.admission_date,
                "discharge_date": note.discharge_date
            }
        )

    @staticmethod
    def extract_medication_nodes(note: DischargeNote) -> List[GraphNode]:
        """Extract medication nodes from discharge note."""
        medication_nodes = []

        for med in note.medications:
            node = GraphNode(
                label="Medication",
                properties={
                    "name": med.name,
                    "dosage": med.dosage,
                    "route": med.route,
                }
            )
            medication_nodes.append(node)

        return medication_nodes

    @staticmethod
    def extract_diagnosis_nodes(note: DischargeNote) -> List[GraphNode]:
        """Extract diagnosis nodes from discharge note."""
        diagnosis_nodes = []

        for diagnosis in note.diagnoses:
            node = GraphNode(
                label="Diagnosis",
                properties={
                    "name": diagnosis,
                }
            )
            diagnosis_nodes.append(node)

        return diagnosis_nodes

    @staticmethod
    def extract_schedule_nodes(note: DischargeNote) -> List[Tuple[GraphNode, Medication]]:
        """Extract schedule nodes from medications."""
        schedule_nodes = []

        for med in note.medications:
            if med.frequency or med.instructions:
                schedule_node = GraphNode(
                    label="Schedule",
                    properties={
                        "frequency": med.frequency,
                        "timing": med.instructions,
                        "instructions": med.instructions,
                    }
                )
                schedule_nodes.append((schedule_node, med))

        return schedule_nodes

    @staticmethod
    def extract_advice_nodes(note: DischargeNote) -> List[GraphNode]:
        """Extract advice nodes from discharge instructions."""
        if not note.instructions:
            return []

        lines = [line.strip() for line in note.instructions.split('\n') if line.strip()]

        advice_nodes = []
        for line in lines:
            if line.startswith('-') or line.startswith('•'):
                line = line[1:].strip()

            category = DischargeNoteExtractor._categorize_advice(line)

            node = GraphNode(
                label="Advice",
                properties={
                    "text": line,
                    "category": category,
                }
            )
            advice_nodes.append(node)

        return advice_nodes

    @staticmethod
    def _categorize_advice(text: str) -> str:
        """Categorize advice based on content."""
        text_lower = text.lower()

        if any(word in text_lower for word in ['follow up', 'appointment', 'visit']):
            return 'followup'
        elif any(word in text_lower for word in ['diet', 'eat', 'food', 'nutrition']):
            return 'diet'
        elif any(word in text_lower for word in ['exercise', 'activity', 'walk']):
            return 'activity'
        elif any(word in text_lower for word in ['monitor', 'check', 'measure', 'test']):
            return 'monitoring'
        elif any(word in text_lower for word in ['medication', 'drug', 'take', 'dose']):
            return 'medication'
        else:
            return 'general'

    @staticmethod
    def extract_all_entities(
        note: DischargeNote
    ) -> Tuple[List[GraphNode], List[GraphRelationship]]:
        """
        Extract all entities and relationships from a discharge note.

        Returns:
            Tuple of (nodes, relationships)
        """
        all_nodes = []
        all_relationships = []

        patient_node = DischargeNoteExtractor.extract_patient_node(note)
        all_nodes.append(patient_node)

        medication_nodes = DischargeNoteExtractor.extract_medication_nodes(note)
        all_nodes.extend(medication_nodes)

        for med_node in medication_nodes:
            rel = GraphRelationship(
                from_node=patient_node,
                rel_type="TAKES",
                to_node=med_node
            )
            all_relationships.append(rel)

        diagnosis_nodes = DischargeNoteExtractor.extract_diagnosis_nodes(note)
        all_nodes.extend(diagnosis_nodes)

        for diag_node in diagnosis_nodes:
            rel = GraphRelationship(
                from_node=patient_node,
                rel_type="HAS_DIAGNOSIS",
                to_node=diag_node
            )
            all_relationships.append(rel)

        schedule_data = DischargeNoteExtractor.extract_schedule_nodes(note)
        for schedule_node, medication in schedule_data:
            all_nodes.append(schedule_node)

            med_node = next(
                (n for n in medication_nodes if n.properties['name'] == medication.name),
                None
            )

            if med_node:
                rel = GraphRelationship(
                    from_node=med_node,
                    rel_type="HAS_SCHEDULE",
                    to_node=schedule_node
                )
                all_relationships.append(rel)

        advice_nodes = DischargeNoteExtractor.extract_advice_nodes(note)
        all_nodes.extend(advice_nodes)

        for advice_node in advice_nodes:
            rel = GraphRelationship(
                from_node=patient_node,
                rel_type="RECEIVED_ADVICE",
                to_node=advice_node
            )
            all_relationships.append(rel)

            for med_node in medication_nodes:
                if med_node.properties['name'].lower() in advice_node.properties['text'].lower():
                    med_rel = GraphRelationship(
                        from_node=advice_node,
                        rel_type="ABOUT_MEDICATION",
                        to_node=med_node
                    )
                    all_relationships.append(med_rel)

        return all_nodes, all_relationships


class DrugBankExtractor:
    """Extract graph entities from DrugBank data."""

    @staticmethod
    def extract_medication_node(drug: DrugInfo) -> GraphNode:
        """Extract medication node from DrugBank data."""
        return GraphNode(
            label="Medication",
            properties={
                "name": drug.name,
                "drugbank_id": drug.drugbank_id,
                "description": drug.description,
                "indication": drug.indication,
                "pharmacodynamics": drug.pharmacodynamics,
                "mechanism": drug.mechanism,
                "metabolism": drug.metabolism,
                "toxicity": drug.toxicity,
            }
        )

    @staticmethod
    def extract_all_medications(drugs: List[DrugInfo]) -> List[GraphNode]:
        """Extract all medication nodes from DrugBank data."""
        return [DrugBankExtractor.extract_medication_node(drug) for drug in drugs]


class InteractionExtractor:
    """Extract drug-drug interactions (to be expanded with real interaction data)."""

    KNOWN_INTERACTIONS = {
        ('Warfarin', 'Aspirin'): {
            'severity': 'severe',
            'description': 'Increased risk of bleeding'
        },
        ('Lisinopril', 'Metformin'): {
            'severity': 'moderate',
            'description': 'Potential for hypoglycemia'
        },
    }

    @staticmethod
    def extract_interaction_relationships(
        medication_nodes: List[GraphNode]
    ) -> List[GraphRelationship]:
        """
        Extract drug interaction relationships.

        Note: This is a simplified version. In production, you would:
        1. Use DrugBank interactions data
        2. Query external APIs (e.g., RxNorm, OpenFDA)
        3. Use NLP on drug interaction databases
        """
        relationships = []

        med_names = [node.properties['name'] for node in medication_nodes]

        for (drug1, drug2), interaction_data in InteractionExtractor.KNOWN_INTERACTIONS.items():
            node1 = next((n for n in medication_nodes if n.properties['name'] == drug1), None)
            node2 = next((n for n in medication_nodes if n.properties['name'] == drug2), None)

            if node1 and node2:
                rel = GraphRelationship(
                    from_node=node1,
                    rel_type="INTERACTS_WITH",
                    to_node=node2,
                    properties=interaction_data
                )
                relationships.append(rel)

        return relationships


if __name__ == "__main__":
    from src.data.parsers import DischargeNoteParser

    sample_text = """
DISCHARGE SUMMARY

Patient Name: [REDACTED]
MRN: TEST123
Date of Admission: 01/15/2024
Date of Discharge: 01/20/2024

DISCHARGE DIAGNOSES:
1. Type 2 Diabetes Mellitus
2. Hypertension

MEDICATIONS ON DISCHARGE:
1. Metformin 500mg - Take 1 tablet by mouth twice daily with meals
2. Lisinopril 10mg - Take 1 tablet by mouth once daily in the morning

DISCHARGE INSTRUCTIONS:
- Monitor blood glucose levels twice daily
- Follow up with primary care physician in 1 week
- Take Metformin with meals to reduce stomach upset
    """

    print("Testing entity extraction...")

    note = DischargeNoteParser.parse_text(sample_text)
    nodes, relationships = DischargeNoteExtractor.extract_all_entities(note)

    print(f"\nExtracted {len(nodes)} nodes:")
    for node in nodes:
        print(f"  {node.label}: {node.properties}")

    print(f"\nExtracted {len(relationships)} relationships:")
    for rel in relationships:
        print(f"  ({rel.from_node.label})-[:{rel.rel_type}]->({rel.to_node.label})")
