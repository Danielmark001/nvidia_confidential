"""
LangChain tools for querying the medication knowledge graph.
Function-calling tools for the LLM agent.
"""

from typing import Optional, List
from langchain_core.tools import tool

from src.utils.logger import get_logger
from src.utils.exceptions import MedicationNotFoundError, QueryError
from src.constants import DEFAULT_MEDICATION_CANDIDATES_LIMIT
from src.kg.queries import (
    MedicationQueryBuilder,
    PatientQueryBuilder,
    AdviceQueryBuilder,
    DrugInfoQueryBuilder,
)
from src.retrieval.query_executor import get_query_executor

logger = get_logger(__name__)


def sanitize_unicode(text: str) -> str:
    """Remove or replace problematic Unicode characters that cause encoding issues."""
    if not text:
        return text

    replacements = {
        '\u2265': '>=',  # greater than or equal
        '\u2264': '<=',  # less than or equal
        '\u00b1': '+/-',  # plus-minus
        '\u03bc': 'u',  # micro
        '\u2022': '*',  # bullet
        '\u2013': '-',  # en dash
        '\u2014': '--',  # em dash
        '\u2019': "'",  # right single quotation
        '\u201c': '"',  # left double quotation
        '\u201d': '"',  # right double quotation
    }

    for unicode_char, replacement in replacements.items():
        text = text.replace(unicode_char, replacement)

    text = text.encode('ascii', 'ignore').decode('ascii')

    return text


class MedicationToolHelpers:
    """Helper functions for medication tools."""

    @staticmethod
    def get_medication_candidates(
        medication_name: str,
        limit: int = DEFAULT_MEDICATION_CANDIDATES_LIMIT
    ) -> List[str]:
        """
        Get candidate medication names from the knowledge graph using fuzzy matching.

        Args:
            medication_name: Name of medication to search for
            limit: Maximum number of candidates to return

        Returns:
            List of matching medication names
        """
        try:
            executor = get_query_executor()
            query, params = MedicationQueryBuilder.find_medication_by_name(
                medication_name,
                limit
            )
            results = executor.execute(query, params)
            candidates = [result['name'] for result in results if result.get('name')]
            logger.info(f"Found {len(candidates)} medication candidates for '{medication_name}'")
            return candidates

        except QueryError as e:
            logger.error(f"Error finding medication candidates: {e}")
            return []

    @staticmethod
    def format_medication_response(medication_name: str, results: List) -> str:
        """Format medication query results into user-friendly response."""
        if not results:
            return f"No dosage information found for {medication_name}."

        response_parts = []
        for result in results:
            med = result.get('medication', medication_name)
            dosage = result.get('dosage', 'dosage not specified')
            route = result.get('route', 'route not specified')
            frequency = result.get('frequency', 'frequency not specified')
            instructions = result.get('instructions', '')

            response = f"{med} - {dosage}"
            if route and route != 'route not specified':
                response += f", {route}"
            if frequency and frequency != 'frequency not specified':
                response += f", {frequency}"
            if instructions:
                response += f" ({instructions})"

            response_parts.append(response)

        return sanitize_unicode("\n".join(response_parts))


@tool
def get_medication_dosage(
    medication_name: str,
    patient_id: Optional[str] = None
) -> str:
    """
    Get dosage and schedule information for a medication.

    Useful when a patient asks:
    - "How should I take [medication]?"
    - "What is the dosage for [medication]?"
    - "When should I take [medication]?"
    - "How many times a day should I take [medication]?"

    Args:
        medication_name: Name of the medication
        patient_id: Optional patient ID for patient-specific dosing

    Returns:
        Formatted string with dosage and schedule information
    """
    try:
        candidates = MedicationToolHelpers.get_medication_candidates(medication_name)

        if not candidates:
            return f"I couldn't find any medication matching '{medication_name}' in the knowledge graph. Please check the spelling or try a different name."

        medication_name = candidates[0]

        executor = get_query_executor()
        query, params = MedicationQueryBuilder.get_medication_schedule(
            medication_name,
            patient_id
        )
        results = executor.execute(query, params)

        return sanitize_unicode(MedicationToolHelpers.format_medication_response(medication_name, results))

    except Exception as e:
        logger.error(f"Error retrieving medication dosage: {e}")
        return f"Error retrieving dosage information: {e}"


@tool
def get_drug_interactions(medication_name: str) -> str:
    """
    Check for drug-drug interactions with a specific medication.

    Useful when a patient asks:
    - "What medications interact with [medication]?"
    - "Can I take [medication] with other drugs?"
    - "Are there any dangerous interactions with [medication]?"
    - "What should I avoid while taking [medication]?"

    Args:
        medication_name: Name of the medication to check

    Returns:
        Formatted string with interaction information
    """
    try:
        candidates = MedicationToolHelpers.get_medication_candidates(medication_name)

        if not candidates:
            return f"I couldn't find any medication matching '{medication_name}' in the knowledge graph."

        medication_name = candidates[0]

        executor = get_query_executor()
        query, params = MedicationQueryBuilder.get_drug_interactions(medication_name)
        results = executor.execute(query, params)

        if not results:
            return f"No known drug interactions found for {medication_name} in the knowledge graph."

        response = f"Known interactions for {medication_name}:\n\n"

        for result in results:
            interacting_drug = result.get('interacting_drug', 'Unknown drug')
            severity = result.get('severity', 'Unknown')
            description = result.get('description', 'No description available')

            response += f"- {interacting_drug} (Severity: {severity})\n"
            response += f"  {description}\n\n"

        return sanitize_unicode(response.strip())

    except Exception as e:
        logger.error(f"Error checking drug interactions: {e}")
        return f"Error checking drug interactions: {e}"


@tool
def get_medication_info(medication_name: str) -> str:
    """
    Get detailed information about a medication from DrugBank.

    Useful when a patient asks:
    - "What is [medication] used for?"
    - "How does [medication] work?"
    - "What should I know about [medication]?"
    - "Tell me about [medication]"

    Args:
        medication_name: Name of the medication

    Returns:
        Formatted string with medication information
    """
    try:
        candidates = MedicationToolHelpers.get_medication_candidates(medication_name)

        if not candidates:
            return f"I couldn't find any medication matching '{medication_name}' in the knowledge graph."

        medication_name = candidates[0]

        executor = get_query_executor()
        query, params = DrugInfoQueryBuilder.get_drug_info(medication_name)
        results = executor.execute(query, params)

        if not results:
            return f"No detailed information found for {medication_name}."

        result = results[0]
        response = f"Information about {result.get('medication', medication_name)}:\n\n"

        if result.get('description'):
            response += f"Description: {result['description']}\n\n"

        if result.get('indication'):
            response += f"Indication: {result['indication']}\n\n"

        if result.get('mechanism'):
            response += f"Mechanism: {result['mechanism']}\n\n"

        if result.get('pharmacodynamics'):
            response += f"Pharmacodynamics: {result['pharmacodynamics']}\n\n"

        return sanitize_unicode(response.strip())

    except Exception as e:
        logger.error(f"Error retrieving medication information: {e}")
        return f"Error retrieving medication information: {e}"


@tool
def get_patient_medications(patient_id: str) -> str:
    """
    Get all medications prescribed to a specific patient.

    Useful when a patient asks:
    - "What medications am I taking?"
    - "List my medications"
    - "What drugs am I on?"

    Args:
        patient_id: Patient identifier

    Returns:
        Formatted string with patient's medication list
    """
    try:
        executor = get_query_executor()
        query, params = PatientQueryBuilder.get_patient_medications(patient_id)
        results = executor.execute(query, params)

        if not results:
            return f"No medications found for patient {patient_id}."

        response = f"Medications for patient {patient_id}:\n\n"

        for i, result in enumerate(results, 1):
            med = result.get('medication', 'Unknown medication')
            dosage = result.get('dosage', 'dosage not specified')
            route = result.get('route', '')
            frequency = result.get('frequency', '')
            instructions = result.get('instructions', '')

            response += f"{i}. {med} - {dosage}"

            if route:
                response += f", {route}"

            if frequency:
                response += f", {frequency}"

            if instructions:
                response += f" ({instructions})"

            response += "\n"

        return sanitize_unicode(response.strip())

    except Exception as e:
        logger.error(f"Error retrieving patient medications: {e}")
        return f"Error retrieving patient medications: {e}"


@tool
def search_discharge_advice(
    search_term: str,
    medication_name: Optional[str] = None
) -> str:
    """
    Search for discharge advice and instructions.

    Useful when a patient asks:
    - "What should I do about [topic]?"
    - "What are my discharge instructions?"
    - "What advice did the doctor give me?"
    - "What should I monitor?"

    Args:
        search_term: Topic or keyword to search for (e.g., "diet", "exercise", "monitoring")
        medication_name: Optional medication name to filter advice

    Returns:
        Formatted string with relevant advice
    """
    try:
        executor = get_query_executor()
        query, params = AdviceQueryBuilder.search_advice(
            search_term,
            medication_name
        )
        results = executor.execute(query, params)

        if not results:
            return f"No advice found related to '{search_term}'."

        response = f"Discharge advice related to '{search_term}':\n\n"

        for i, result in enumerate(results, 1):
            advice_text = result.get('advice', 'No advice text')
            category = result.get('category', 'general')

            response += f"{i}. [{category}] {advice_text}\n"

            if medication_name and result.get('medication'):
                response += f"   Related medication: {result['medication']}\n"
            elif result.get('medications'):
                meds = result['medications']
                if meds:
                    response += f"   Related medications: {', '.join(meds)}\n"

        return sanitize_unicode(response.strip())

    except Exception as e:
        logger.error(f"Error searching advice: {e}")
        return f"Error searching advice: {e}"


@tool
def check_contraindications(
    medication_name: Optional[str] = None,
    diagnosis: Optional[str] = None
) -> str:
    """
    Check if a medication is contraindicated for a specific condition.

    Useful when a patient asks:
    - "Can I take [medication] if I have [condition]?"
    - "Is [medication] safe for [condition]?"
    - "What conditions should avoid [medication]?"

    Args:
        medication_name: Name of the medication (optional)
        diagnosis: Name of the medical condition (optional)

    Returns:
        Formatted string with contraindication information
    """
    try:
        if not medication_name and not diagnosis:
            return "Please provide either a medication name or a diagnosis to check contraindications."

        executor = get_query_executor()
        query, params = MedicationQueryBuilder.get_contraindications(
            medication_name,
            diagnosis
        )
        results = executor.execute(query, params)

        if not results:
            if medication_name and diagnosis:
                return f"No contraindications found between {medication_name} and {diagnosis}."
            elif medication_name:
                return f"No contraindications found for {medication_name}."
            else:
                return f"No contraindications found for {diagnosis}."

        response = "Contraindications found:\n\n"

        for result in results:
            med = result.get('medication', 'Unknown medication')
            diag = result.get('diagnosis', 'Unknown condition')
            severity = result.get('severity', 'Unknown')
            reason = result.get('reason', 'No reason provided')

            response += f"- {med} is contraindicated for {diag}\n"
            response += f"  Severity: {severity}\n"
            response += f"  Reason: {reason}\n\n"

        return sanitize_unicode(response.strip())

    except Exception as e:
        logger.error(f"Error checking contraindications: {e}")
        return f"Error checking contraindications: {e}"


MEDICATION_TOOLS = [
    get_medication_dosage,
    get_drug_interactions,
    get_medication_info,
    get_patient_medications,
    search_discharge_advice,
    check_contraindications,
]


if __name__ == "__main__":
    print("Testing medication tools...")
    print("=" * 60)

    print("\nTesting get_medication_dosage...")
    result = get_medication_dosage.invoke({"medication_name": "metformin"})
    print(result)

    print("\n" + "=" * 60)
    print("\nTesting get_drug_interactions...")
    result = get_drug_interactions.invoke({"medication_name": "warfarin"})
    print(result)
