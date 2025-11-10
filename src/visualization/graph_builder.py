"""Build graph data structures for visualization."""

from typing import List, Dict, Tuple


def build_medication_subgraph(
    medication_name: str,
    interacting_drugs: List[Dict] = None,
    contraindications: List[Dict] = None
) -> Tuple[List[Dict], List[Dict]]:
    """
    Build a medication-centric graph for visualization.

    Args:
        medication_name: Name of the medication
        interacting_drugs: List of interacting medications
        contraindications: List of contraindicated conditions

    Returns:
        Tuple of (nodes, edges)
    """
    nodes = []
    edges = []

    # Main medication node
    nodes.append({
        "id": medication_name,
        "label": medication_name,
        "type": "Medication",
        "color": "#667eea",
        "size": 40,
        "title": f"Medication: {medication_name}"
    })

    # Add interacting drugs
    if interacting_drugs:
        for interaction in interacting_drugs:
            drug_name = interaction.get("interacting_med", "Unknown")
            severity = interaction.get("severity", "unknown")

            # Determine color based on severity
            severity_color = {
                "severe": "#ff4757",
                "moderate": "#ffa502",
                "mild": "#ffb347",
                "unknown": "#cccccc"
            }.get(severity, "#cccccc")

            nodes.append({
                "id": drug_name,
                "label": drug_name,
                "type": "Medication",
                "color": severity_color,
                "size": 30,
                "title": f"Interacts (Severity: {severity})"
            })

            edges.append({
                "from": medication_name,
                "to": drug_name,
                "label": f"INTERACTS ({severity})",
                "color": severity_color,
                "title": f"Drug-drug interaction - Severity: {severity}"
            })

    # Add contraindications
    if contraindications:
        for contraind in contraindications:
            condition = contraind.get("name", "Unknown")

            nodes.append({
                "id": condition,
                "label": condition,
                "type": "Diagnosis",
                "color": "#ffd43b",
                "size": 30,
                "title": f"Condition: {condition}"
            })

            edges.append({
                "from": medication_name,
                "to": condition,
                "label": "CONTRAINDICATES",
                "color": "#ffd43b",
                "title": "This medication is contraindicated for this condition"
            })

    return nodes, edges


def build_patient_medication_network(
    patient_name: str,
    medications: List[Dict] = None,
    diagnoses: List[Dict] = None,
    interactions: List[Dict] = None
) -> Tuple[List[Dict], List[Dict]]:
    """
    Build a patient-centric medication network for visualization.

    Args:
        patient_name: Name/ID of the patient
        medications: List of medications the patient takes
        diagnoses: List of patient diagnoses
        interactions: List of interactions between medications

    Returns:
        Tuple of (nodes, edges)
    """
    nodes = []
    edges = []

    # Patient node
    nodes.append({
        "id": patient_name,
        "label": patient_name,
        "type": "Patient",
        "color": "#51cf66",
        "size": 40,
        "title": f"Patient: {patient_name}"
    })

    # Add medications
    med_ids = set()
    if medications:
        for med in medications:
            med_name = med.get("name", "Unknown")
            med_ids.add(med_name)
            dosage = med.get("dosage", "")
            frequency = med.get("frequency", "")

            nodes.append({
                "id": med_name,
                "label": med_name,
                "type": "Medication",
                "color": "#667eea",
                "size": 30,
                "title": f"{med_name}\nDosage: {dosage}\nFrequency: {frequency}"
            })

            edges.append({
                "from": patient_name,
                "to": med_name,
                "label": "TAKES",
                "color": "#667eea",
                "title": f"Patient takes {med_name}"
            })

    # Add diagnoses
    if diagnoses:
        for diag in diagnoses:
            diag_name = diag.get("name", "Unknown")

            nodes.append({
                "id": diag_name,
                "label": diag_name,
                "type": "Diagnosis",
                "color": "#ffd43b",
                "size": 30,
                "title": f"Diagnosis: {diag_name}"
            })

            edges.append({
                "from": patient_name,
                "to": diag_name,
                "label": "HAS_DIAGNOSIS",
                "color": "#ffd43b",
                "title": f"Patient diagnosed with {diag_name}"
            })

    # Add drug-drug interactions
    if interactions:
        for interaction in interactions:
            from_med = interaction.get("from_medication")
            to_med = interaction.get("to_medication")
            severity = interaction.get("severity", "unknown")

            if from_med and to_med and from_med in med_ids and to_med in med_ids:
                severity_color = {
                    "severe": "#ff4757",
                    "moderate": "#ffa502",
                    "mild": "#ffb347",
                    "unknown": "#ff6b6b"
                }.get(severity, "#ff6b6b")

                edges.append({
                    "from": from_med,
                    "to": to_med,
                    "label": f"INTERACTS ({severity})",
                    "color": severity_color,
                    "dashes": True,
                    "title": f"Interaction between {from_med} and {to_med} - Severity: {severity}"
                })

    return nodes, edges


def build_simple_graph(nodes_data: List[Dict], edges_data: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """
    Normalize arbitrary graph data for visualization.

    Args:
        nodes_data: List of node definitions
        edges_data: List of edge definitions

    Returns:
        Tuple of (normalized_nodes, normalized_edges)
    """
    # Ensure all nodes have required properties
    normalized_nodes = []
    for node in nodes_data:
        normalized_nodes.append({
            "id": node.get("id", ""),
            "label": node.get("label", node.get("id", "")),
            "type": node.get("type", "Unknown"),
            "color": node.get("color", "#999999"),
            "size": node.get("size", 25),
            "title": node.get("title", node.get("label", ""))
        })

    # Ensure all edges have required properties
    normalized_edges = []
    for edge in edges_data:
        normalized_edges.append({
            "from": edge.get("from", ""),
            "to": edge.get("to", ""),
            "label": edge.get("label", ""),
            "color": edge.get("color", "#999999"),
            "title": edge.get("title", edge.get("label", "")),
            "dashes": edge.get("dashes", False)
        })

    return normalized_nodes, normalized_edges


def get_graph_config() -> Dict:
    """Get default configuration for graph visualization."""
    return {
        "height": 500,
        "nodeHighlightBehavior": True,
        "highlightColor": "#667eea",
        "directed": True,
        "physics": {
            "enabled": True,
            "barnesHut": {
                "gravitationalConstant": -15000,
                "springLength": 200,
                "springConstant": 0.02
            },
            "minVelocity": 0.75,
            "stabilization": {"iterations": 200}
        },
        "margin": {"top": 20, "right": 20, "bottom": 20, "left": 20},
        "backgroundColor": "#ffffff"
    }
