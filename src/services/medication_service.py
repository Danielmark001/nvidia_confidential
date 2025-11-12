"""Service layer for medication query processing."""

from typing import Dict, List, Optional
from openai import OpenAI
from neo4j import GraphDatabase


class MedicationQueryService:
    """Service for processing medication queries using NVIDIA NIM and Neo4j."""

    def __init__(self, nvidia_api_key: str, neo4j_uri: str, neo4j_user: str, neo4j_pass: str):
        """Initialize the medication query service."""
        self.nvidia_api_key = nvidia_api_key
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_pass = neo4j_pass

        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=self.nvidia_api_key
        )

    def generate_search_terms(self, user_query: str, model: str) -> str:
        """Generate optimal search terms from user query using LLM."""
        extraction_response = self.client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": """You are a search query generator for a medication database. Given a user's question, generate the optimal search terms that would find relevant medications in a fulltext search.

Consider:
- Medication names (e.g., "insulin", "metformin", "aspirin")
- Medical conditions (e.g., "diabetes", "hypertension", "pain")
- Drug classes (e.g., "antibiotics", "statins", "beta blockers")
- Symptoms being treated (e.g., "high blood pressure", "fever", "inflammation")
- Generic concepts (e.g., "blood sugar", "cholesterol")

Return 2-5 relevant search terms separated by spaces. Choose terms that would match medication names, descriptions, or indications.

Examples:
- "What is insulin?" -> "insulin diabetes"
- "Tell me about metformin" -> "metformin"
- "What treats high blood pressure?" -> "hypertension blood pressure"
- "I have diabetes, what are my options?" -> "diabetes glucose insulin"
- "What's good for pain?" -> "pain analgesic"
- "Alternatives to aspirin?" -> "aspirin antiplatelet"

Return ONLY the search terms, no explanation."""
                },
                {
                    "role": "user",
                    "content": user_query
                }
            ],
            temperature=0.0,
            max_tokens=50
        )

        return extraction_response.choices[0].message.content.strip()

    def query_knowledge_graph(self, search_terms: str, limit: int = 3) -> List[Dict]:
        """Query Neo4j knowledge graph for medication information."""
        driver = GraphDatabase.driver(
            self.neo4j_uri,
            auth=(self.neo4j_user, self.neo4j_pass)
        )

        with driver.session() as session:
            result = session.run("""
                CALL db.index.fulltext.queryNodes('medication_fulltext', $search_term)
                YIELD node, score
                RETURN node.name as name,
                       node.description as description,
                       node.indication as indication
                LIMIT $limit
            """, search_term=search_terms, limit=limit)

            kg_results = []
            for record in result:
                kg_results.append({
                    "name": record["name"],
                    "description": record["description"][:500] if record["description"] else "",
                    "indication": record["indication"][:500] if record["indication"] else ""
                })

        driver.close()
        return kg_results

    def format_context(self, kg_results: List[Dict]) -> str:
        """Format knowledge graph results into context string."""
        if not kg_results:
            return "No medication information found in the knowledge graph.\n"

        context = "Knowledge Graph Information:\n\n"
        for i, med in enumerate(kg_results, 1):
            context += f"{i}. {med['name']}\n"
            if med['description']:
                desc = med['description'].encode('ascii', 'ignore').decode('ascii')
                context += f"   Description: {desc}\n"
            if med['indication']:
                indic = med['indication'].encode('ascii', 'ignore').decode('ascii')
                context += f"   Indication: {indic}\n"
            context += "\n"

        return context

    def generate_system_prompt(self, response_style: str, patient_context: Optional[Dict] = None) -> str:
        """Generate system prompt based on response style and patient context."""
        if response_style == "Detailed (Structured)":
            system_prompt = """You are an expert medical information assistant who explains medication information in a natural, conversational way.

CRITICAL RULES:
1. ONLY use information explicitly stated in the Knowledge Graph Data provided
2. NEVER infer, assume, or add information not present in the data
3. Explain naturally as if talking to a patient, but stay factual
4. Make connections between different aspects of the medication when the data supports it
5. If information is not in the data, simply say you don't have that information
6. Do not use bold text, asterisks, or any markdown formatting
7. Do not create rigid sections with labels like "Medication:", "Citation:", or "Disclaimer:"
8. Weave the information together in a flowing explanation

Your approach:
- Start by directly addressing what the medication is and does
- Explain how it works if that information is in the data
- Connect different pieces of information naturally (e.g., how the mechanism relates to what it treats)
- Use patient-friendly language, explaining medical terms naturally in context
- End with a brief note that this is informational and they should consult their healthcare provider

Quality targets:
- Zero hallucination (only use provided data)
- Natural, flowing explanations
- Clear connections between related concepts"""

        elif response_style == "Concise (Brief)":
            system_prompt = """You are a medication information assistant who gives brief, natural explanations.

Guidelines:
- Provide short, conversational answers based on the knowledge graph data
- Use 2-3 sentences maximum
- Explain the key point naturally without rigid structure
- Only use information from the provided data
- Keep it simple and patient-friendly
- Do not use bold text, asterisks, or markdown formatting
- End with a brief reminder to consult a healthcare provider"""

        else:
            system_prompt = """You are an expert clinical pharmacologist who explains medication information conversationally but with technical precision.

Guidelines:
- Use precise medical and pharmacological terminology naturally in context
- Explain mechanisms, pathways, and drug classes in a flowing narrative
- Connect pharmacokinetic and pharmacodynamic information when discussing how medications work
- Reference the knowledge graph data accurately but weave it into natural explanations
- Assume audience has medical background but still make logical connections clear
- Include clinical considerations naturally in the explanation
- Do not use bold text, asterisks, or markdown formatting
- Do not create rigid sections or labels"""

        if patient_context:
            patient = patient_context
            system_prompt += f"""

PATIENT CONTEXT (Demo Mode):
You are assisting a patient with the following profile:
- Name: {patient.get('name', 'Patient')}
- Age: {patient.get('age', 'Unknown')}
- Diagnoses: {', '.join(patient.get('diagnoses', []))}
- Current Medications: {', '.join(patient.get('medications', []))}

Consider this patient's specific situation when providing medication information. Be especially careful about drug interactions with their current medications."""

        return system_prompt

    def generate_response(
        self,
        user_query: str,
        context: str,
        model: str,
        temperature: float,
        top_p: float,
        max_tokens: int,
        response_style: str,
        patient_context: Optional[Dict] = None
    ) -> str:
        """Generate AI response using NVIDIA NIM."""
        system_prompt = self.generate_system_prompt(response_style, patient_context)

        few_shot = """EXAMPLE:
KG Data: "Metformin - Description: Biguanide that decreases hepatic glucose production. Indication: Type 2 diabetes mellitus."
Question: "What is Metformin used for?"
Answer: "Metformin is used to treat type 2 diabetes mellitus. It works by decreasing the amount of glucose your liver produces, which helps improve blood sugar control. As a biguanide medication, it's particularly effective for managing glycemic levels in diabetic patients. Remember to consult your healthcare provider for personalized advice about this medication."

---"""

        user_message = f"""{few_shot}

Knowledge Graph Data (ONLY SOURCE OF TRUTH):
{context}

Patient Question: {user_query}

Answer following the EXAMPLE format. Use ONLY the data provided above."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]

        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens
        )

        return response.choices[0].message.content

    def process_query(
        self,
        user_query: str,
        model: str,
        temperature: float,
        top_p: float,
        max_tokens: int,
        response_style: str,
        patient_context: Optional[Dict] = None
    ) -> Dict:
        """Process a complete medication query."""
        search_terms = self.generate_search_terms(user_query, model)
        kg_results = self.query_knowledge_graph(search_terms)
        context = self.format_context(kg_results)

        answer = self.generate_response(
            user_query,
            context,
            model,
            temperature,
            top_p,
            max_tokens,
            response_style,
            patient_context
        )

        return {
            "answer": answer,
            "context": context,
            "medications": [med["name"] for med in kg_results] if kg_results else [],
            "search_terms": search_terms
        }


def create_medication_service(
    nvidia_api_key: str,
    neo4j_uri: str,
    neo4j_user: str,
    neo4j_pass: str
) -> MedicationQueryService:
    """Factory function to create medication query service."""
    return MedicationQueryService(
        nvidia_api_key=nvidia_api_key,
        neo4j_uri=neo4j_uri,
        neo4j_user=neo4j_user,
        neo4j_pass=neo4j_pass
    )
