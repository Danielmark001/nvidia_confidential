"""Patient scenario management for demo mode."""

import json
from typing import List, Dict, Optional
from pathlib import Path


class PatientScenarioManager:
    """Load and manage patient scenarios for demo conversations."""

    def __init__(self, scenarios_file: str = None):
        """
        Initialize patient scenario manager.

        Args:
            scenarios_file: Path to scenarios JSON file
        """
        if scenarios_file is None:
            scenarios_file = Path(__file__).parent.parent.parent / "data" / "scenarios" / "patient_scenarios.json"

        self.scenarios_file = Path(scenarios_file)
        self.scenarios = self._load_scenarios()

    def _load_scenarios(self) -> List[Dict]:
        """Load scenarios from JSON file."""
        if not self.scenarios_file.exists():
            return []

        try:
            with open(self.scenarios_file, 'r') as f:
                data = json.load(f)
                return data.get("scenarios", [])
        except Exception as e:
            print(f"Error loading scenarios: {e}")
            return []

    def get_all_scenarios(self) -> List[Dict]:
        """Get all available patient scenarios."""
        return self.scenarios

    def get_scenario(self, scenario_id: str) -> Optional[Dict]:
        """Get a specific patient scenario by ID."""
        for scenario in self.scenarios:
            if scenario.get("id") == scenario_id:
                return scenario
        return None

    def get_scenario_by_index(self, index: int) -> Optional[Dict]:
        """Get scenario by index."""
        if 0 <= index < len(self.scenarios):
            return self.scenarios[index]
        return None

    def get_scenario_names(self) -> List[str]:
        """Get list of scenario names."""
        return [f"{s['name']} - {s['context']}" for s in self.scenarios]

    def get_scenario_summary(self, scenario: Dict) -> str:
        """Get a brief summary of a scenario."""
        return f"""
**Patient:** {scenario.get('name', 'Unknown')}
**Age:** {scenario.get('age', 'N/A')}
**Reason for hospitalization:** {scenario.get('chief_complaint', 'N/A')}

**Diagnoses:**
{chr(10).join(f"- {d['name']}" for d in scenario.get('diagnoses', []))}

**Current Medications:**
{chr(10).join(f"- {m['name']} ({m.get('dosage', 'N/A')})" for m in scenario.get('medications', []))}
        """

    def get_medications_info(self, scenario: Dict) -> str:
        """Get detailed medication information for a scenario."""
        meds = scenario.get("medications", [])
        med_text = ""

        for med in meds:
            med_text += f"""
**{med['name']}**
- Dosage: {med.get('dosage', 'N/A')}
- Frequency: {med.get('frequency', 'N/A')}
- Route: {med.get('route', 'N/A')}
- Instructions: {med.get('instructions', 'N/A')}
- Indication: {med.get('indication', 'N/A')}
"""

        return med_text

    def get_diagnoses_info(self, scenario: Dict) -> str:
        """Get diagnosis information for a scenario."""
        diagnoses = scenario.get("diagnoses", [])
        diag_text = ""

        for diag in diagnoses:
            diag_text += f"- {diag['name']} (Code: {diag.get('code', 'N/A')})\n"

        return diag_text

    def get_system_context(self, scenario: Dict) -> str:
        """Generate system prompt context for a scenario."""
        return f"""You are assisting a patient who was recently discharged from the hospital.

Patient Information:
- Name: {scenario.get('name', 'Patient')}
- Age: {scenario.get('age', 'N/A')}
- Admission Date: {scenario.get('admission_date', 'N/A')}
- Discharge Date: {scenario.get('discharge_date', 'N/A')}
- Situation: {scenario.get('context', 'N/A')}

Current Diagnoses:
{self.get_diagnoses_info(scenario)}

Current Medications:
{self.get_medications_info(scenario)}

Your role is to provide clear, patient-friendly medical guidance based on this discharge information. Be empathetic, clear, and encourage the patient to contact their healthcare provider for any concerns.
"""

    def get_sample_questions(self, scenario: Dict) -> List[str]:
        """Get sample questions for a scenario."""
        return scenario.get("sample_questions", [])
