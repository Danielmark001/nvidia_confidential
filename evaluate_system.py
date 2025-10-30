"""
Evaluation script for Medication Advisor AI
Measures F1-score and Citation Precision against gold answers

Target Metrics (from README.md):
- Answer correctness (F1-score): ≥0.80
- Citation quality (Graph Precision): ≥0.90
"""

import os
import json
import sys
from dotenv import load_dotenv
from neo4j import GraphDatabase
from openai import OpenAI
from sklearn.metrics import precision_recall_fscore_support
import re

if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'ignore')

load_dotenv()

# Load test questions
with open('data/questions/test_questions.json', 'r') as f:
    data = json.load(f)
    questions = data['questions']

# Initialize clients
driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
)

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("NVIDIA_API_KEY")
)

def query_knowledge_graph(question):
    """Query Neo4j for relevant medication data"""
    with driver.session() as session:
        result = session.run("""
            CALL db.index.fulltext.queryNodes('medication_fulltext', $search_term)
            YIELD node, score
            RETURN node.name as name,
                   node.description as description,
                   node.indication as indication,
                   score
            LIMIT 3
        """, search_term=question)

        kg_results = []
        cited_medications = []
        for record in result:
            kg_results.append({
                "name": record["name"],
                "description": record["description"][:500] if record["description"] else "",
                "indication": record["indication"][:500] if record["indication"] else "",
                "score": record["score"]
            })
            cited_medications.append(record["name"])

        return kg_results, cited_medications

def generate_answer(question, kg_results):
    """Generate answer using NVIDIA NIM LLM"""
    if kg_results:
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
    else:
        context = "No medication information found in the knowledge graph.\n"

    system_prompt = """You are an expert medical information assistant specializing in medication guidance.

CRITICAL RULES FOR HIGH ACCURACY (Target F1≥0.80, Citation Precision≥0.90):
1. ONLY use information explicitly stated in the Knowledge Graph Data provided
2. NEVER infer, assume, or add information not present in the data
3. ALWAYS quote or paraphrase directly from the descriptions and indications
4. CITE the medication name you're referencing
5. If information is not in the data, state: "This information is not available in the knowledge graph"

Response structure:
- Start with the medication name
- Quote/paraphrase key facts from description and indication
- End with citation to knowledge graph"""

    few_shot = """EXAMPLE:
KG Data: "Metformin - Description: Biguanide that decreases hepatic glucose production. Indication: Type 2 diabetes mellitus."
Question: "What is Metformin used for?"
Answer: "Metformin is indicated for type 2 diabetes mellitus. It decreases hepatic glucose production and improves glycemic control. Source: Knowledge Graph - Metformin"

---"""

    user_message = f"""{few_shot}

Knowledge Graph Data (ONLY SOURCE OF TRUTH):
{context}

Patient Question: {question}

Answer following the EXAMPLE format. Use ONLY the data provided above."""

    response = client.chat.completions.create(
        model="meta/llama-3.3-70b-instruct",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        temperature=0.05,
        top_p=0.95,
        max_tokens=768
    )

    return response.choices[0].message.content

def tokenize(text):
    """Simple tokenization for F1 calculation"""
    return set(re.findall(r'\b\w+\b', text.lower()))

def calculate_f1(gold_answer, system_answer):
    """Calculate token-level F1 score"""
    gold_tokens = tokenize(gold_answer)
    system_tokens = tokenize(system_answer)

    if not gold_tokens or not system_tokens:
        return 0.0, 0.0, 0.0

    true_positives = len(gold_tokens & system_tokens)
    false_positives = len(system_tokens - gold_tokens)
    false_negatives = len(gold_tokens - system_tokens)

    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return precision, recall, f1

def calculate_citation_precision(cited_meds, supporting_keywords):
    """Calculate citation precision based on supporting keywords"""
    if not cited_meds:
        return 0.0

    valid_citations = sum(
        1 for med in cited_meds
        if any(keyword.lower() in med.lower() for keyword in supporting_keywords)
    )

    return valid_citations / len(cited_meds)

def extract_cited_medications(answer):
    """Extract medication names mentioned in the answer"""
    # Simple extraction - looks for capitalized drug names
    med_pattern = r'\b[A-Z][a-z]+(?:cillin|pine|statin|pril|sartan|formin|mycin|zole|xetine|olol)\b'
    cited = re.findall(med_pattern, answer)
    return list(set(cited))

print("=" * 80)
print("MEDICATION ADVISOR AI - EVALUATION")
print("=" * 80)
print(f"Target Metrics:")
print(f"  - Answer F1-score: ≥0.80")
print(f"  - Citation Precision: ≥0.90")
print()

# Full evaluation on all 50 questions
sample_size = len(questions)
print(f"Running evaluation on {sample_size} questions...")
print()

f1_scores = []
citation_precisions = []
results = []

for i, q in enumerate(questions[:sample_size], 1):
    print(f"[{i}/{sample_size}] {q['question']}")

    # Query KG
    kg_results, cited_meds_kg = query_knowledge_graph(q['question'])

    # Generate answer
    system_answer = generate_answer(q['question'], kg_results)

    # Extract citations from answer
    cited_meds_answer = extract_cited_medications(system_answer)
    all_cited = list(set(cited_meds_kg + cited_meds_answer))

    # Calculate F1
    precision, recall, f1 = calculate_f1(q['gold_answer'], system_answer)
    f1_scores.append(f1)

    # Calculate citation precision
    citation_prec = calculate_citation_precision(all_cited, q['supporting_keywords'])
    citation_precisions.append(citation_prec)

    print(f"  F1: {f1:.3f}, Citation Precision: {citation_prec:.3f}")

    results.append({
        'question': q['question'],
        'gold_answer': q['gold_answer'],
        'system_answer': system_answer,
        'f1': f1,
        'citation_precision': citation_prec,
        'cited_medications': all_cited
    })

    print()

driver.close()

# Calculate overall metrics
avg_f1 = sum(f1_scores) / len(f1_scores)
avg_citation = sum(citation_precisions) / len(citation_precisions)

print("=" * 80)
print("EVALUATION RESULTS")
print("=" * 80)
print(f"Average F1-score:         {avg_f1:.3f} (target: ≥0.80)")
print(f"Average Citation Precision: {avg_citation:.3f} (target: ≥0.90)")
print()

if avg_f1 >= 0.80:
    print("✅ F1-score target MET!")
else:
    print(f"⚠️  F1-score below target (gap: {0.80 - avg_f1:.3f})")

if avg_citation >= 0.90:
    print("✅ Citation precision target MET!")
else:
    print(f"⚠️  Citation precision below target (gap: {0.90 - avg_citation:.3f})")

print()

# Save detailed results
with open('evaluation_results.json', 'w', encoding='utf-8') as f:
    json.dump({
        'metadata': {
            'questions_evaluated': sample_size,
            'avg_f1': avg_f1,
            'avg_citation_precision': avg_citation,
            'f1_target': 0.80,
            'citation_target': 0.90,
            'f1_met': avg_f1 >= 0.80,
            'citation_met': avg_citation >= 0.90
        },
        'results': results
    }, f, indent=2, ensure_ascii=False)

print(f"Detailed results saved to: evaluation_results.json")
print()

# Recommendations
print("=" * 80)
print("RECOMMENDATIONS")
print("=" * 80)

if avg_f1 < 0.80:
    print("To improve F1-score:")
    print("  - Use lower temperature (0.05-0.1)")
    print("  - Emphasize exact quoting from knowledge graph")
    print("  - Increase max_tokens for more comprehensive answers")
    print("  - Add few-shot examples in system prompt")

if avg_citation < 0.90:
    print("To improve Citation Precision:")
    print("  - Explicitly require medication name citations")
    print("  - Penalize hallucinated drug names")
    print("  - Improve keyword extraction from gold answers")
    print("  - Add citation format requirements")
