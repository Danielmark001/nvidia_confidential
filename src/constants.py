"""
Constants and configuration values for the medication advisor system.
Centralized place for all magic strings and default values.
"""

import re
from typing import Dict, Tuple

DEFAULT_LLM_MODEL = "meta/llama-3.1-70b-instruct"
DEFAULT_LLM_TEMPERATURE = 0.0
DEFAULT_LLM_MAX_TOKENS = 1024
DEFAULT_NEO4J_URI = "bolt://localhost:7687"
DEFAULT_NEO4J_USERNAME = "neo4j"
DEFAULT_DATA_DIR = "data"
DEFAULT_DRUGBANK_DATA_PATH = "data/drugbank"
DEFAULT_I2B2_DATA_PATH = "data/i2b2_2014"
DEFAULT_LOG_LEVEL = "INFO"

DEFAULT_QUERY_LIMIT = 5
DEFAULT_MEDICATION_CANDIDATES_LIMIT = 3
DEFAULT_CHAT_HISTORY_SIZE = 10
DEFAULT_MAX_AGENT_ITERATIONS = 5

NEO4J_FULLTEXT_INDEX = "medication_fulltext"
NEO4J_CONSTRAINTS = {
    "Patient": ["patient_id"],
    "Medication": ["name", "drugbank_id"],
    "Diagnosis": ["name"],
    "Interaction": ["id"],
}

NODE_LABELS = {
    "PATIENT": "Patient",
    "MEDICATION": "Medication",
    "DIAGNOSIS": "Diagnosis",
    "SCHEDULE": "Schedule",
    "ADVICE": "Advice",
    "INTERACTION": "Interaction",
    "DISCHARGE_NOTE": "DischargeNote",
}

RELATIONSHIP_TYPES = {
    "TAKES": "TAKES",
    "HAS_DIAGNOSIS": "HAS_DIAGNOSIS",
    "HAS_SCHEDULE": "HAS_SCHEDULE",
    "HAS_ADVICE": "HAS_ADVICE",
    "INTERACTS_WITH": "INTERACTS_WITH",
    "FROM_NOTE": "FROM_NOTE",
    "ENRICHED_BY": "ENRICHED_BY",
}

DISCHARGE_NOTE_PATTERNS: Dict[str, str] = {
    "PATIENT_ID_MRN": r'MRN[:\s]+([A-Z0-9]+)',
    "PATIENT_ID": r'Patient\s+ID[:\s]+([A-Z0-9]+)',
    "ADMISSION_DATE": r'Date\s+of\s+admission[:\s]+(\d{1,2}/\d{1,2}/\d{4})',
    "DISCHARGE_DATE": r'Date\s+of\s+discharge[:\s]+(\d{1,2}/\d{1,2}/\d{4})',
    "DIAGNOSES_SECTION": r'DISCHARGE\s+DIAGNOS[IE]S?:(.+?)(?=\n\n|\nMEDICATIONS|\nDISCHARGE\s+MEDICATIONS)',
    "MEDICATIONS_SECTION": r'(?:DISCHARGE\s+)?MEDICATIONS?(?:\s+ON\s+DISCHARGE)?:(.+?)(?=\n\n[A-Z]|\nDISCHARGE\s+INSTRUCTIONS|$)',
    "INSTRUCTIONS_SECTION": r'DISCHARGE\s+INSTRUCTIONS:(.+?)(?=\n\n[A-Z]|$)',
    "MEDICATION_LINE": r'^\d+\.\s+([A-Z][a-zA-Z]+)\s+(\d+\s?m?g)\s*[-–]\s*Take\s+(.+)',
}

MEDICATION_ROUTES = {
    "ORAL": ["by mouth", "orally", "PO"],
    "IV": ["IV", "intravenous"],
    "SUBCUTANEOUS": ["subcutaneous", "SC", "SQ"],
}

MEDICATION_FREQUENCIES = [
    (r'once\s+daily', 'once daily'),
    (r'twice\s+daily', 'twice daily'),
    (r'three\s+times\s+daily', 'three times daily'),
    (r'four\s+times\s+daily', 'four times daily'),
    (r'QD', 'once daily'),
    (r'BID', 'twice daily'),
    (r'TID', 'three times daily'),
    (r'QID', 'four times daily'),
]

MEDICATION_INSTRUCTIONS = [
    ("with meals", "with meals"),
    ("at bedtime", "at bedtime"),
    ("in the morning", "in the morning"),
]

AGENT_SYSTEM_PROMPT = """You are a helpful medication advisor assistant that provides information about medications based on discharge summaries and drug databases.

Your role is to:
1. Answer patient questions about their medications clearly and accurately
2. Provide dosage and schedule information when asked
3. Warn about potential drug interactions
4. Explain what medications are used for
5. Share relevant discharge instructions

Important guidelines:
- ALWAYS cite information from the knowledge graph when providing answers
- If you're unsure or information is not in the knowledge graph, say so clearly
- For medical emergencies, advise patients to contact their healthcare provider immediately
- Be empathetic and patient-friendly in your responses
- Break down complex medical information into simple terms
- If tools require follow-up questions, ask the user for clarification

Remember: You are providing information, not medical advice. Always encourage patients to consult their healthcare provider for medical decisions."""

DRUGBANK_CSV_FIELDS = [
    "drugbank_id",
    "name",
    "description",
    "indication",
    "pharmacodynamics",
    "mechanism_of_action",
    "toxicity",
    "metabolism",
]

VOICE_DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"
VOICE_DEFAULT_MODEL = "eleven_monolingual_v1"
