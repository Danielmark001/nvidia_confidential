"""
Simple test for barebones NVIDIA NIM + Neo4j integration
"""

import os
import sys
from dotenv import load_dotenv

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'ignore')

load_dotenv()

print("=" * 60)
print("Barebones Integration Test")
print("=" * 60)
print()

# Test 1: NVIDIA NIM
print("[1/3] Testing NVIDIA NIM API...")
try:
    from openai import OpenAI

    client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=os.getenv("NVIDIA_API_KEY")
    )

    response = client.chat.completions.create(
        model="meta/llama-3.3-70b-instruct",
        messages=[{"role": "user", "content": "Say hello in one sentence."}],
        temperature=0.2,
        max_tokens=50
    )

    result = response.choices[0].message.content
    print(f"  SUCCESS: {result}")
    print()

except Exception as e:
    print(f"  FAILED: {str(e)}")
    print()
    exit(1)

# Test 2: Neo4j
print("[2/3] Testing Neo4j Knowledge Graph...")
try:
    from neo4j import GraphDatabase

    driver = GraphDatabase.driver(
        os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
    )

    with driver.session() as session:
        result = session.run("MATCH (n:Medication) RETURN count(n) as count")
        med_count = result.single()["count"]

        result = session.run("""
            MATCH (m:Medication)
            WHERE m.name = 'Metformin'
            RETURN m.name as name, m.indication as indication
            LIMIT 1
        """)
        sample = result.single()

    driver.close()

    print(f"  SUCCESS: Connected to Neo4j")
    print(f"  - Medications in database: {med_count:,}")
    if sample:
        print(f"  - Sample: {sample['name']}")
    print()

except Exception as e:
    print(f"  FAILED: {str(e)}")
    print()
    exit(1)

# Test 3: Combined RAG
print("[3/3] Testing RAG: Retrieve from KG + Generate with LLM...")
try:
    from neo4j import GraphDatabase
    from openai import OpenAI

    driver = GraphDatabase.driver(
        os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
    )

    with driver.session() as session:
        result = session.run("""
            CALL db.index.fulltext.queryNodes('medication_fulltext', 'Metformin')
            YIELD node, score
            RETURN node.name as name, node.indication as indication
            LIMIT 1
        """)
        med = result.single()

    driver.close()

    if med:
        context = f"Medication: {med['name']}\nIndication: {med['indication'][:300] if med['indication'] else 'N/A'}"

        client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=os.getenv("NVIDIA_API_KEY")
        )

        response = client.chat.completions.create(
            model="meta/llama-3.3-70b-instruct",
            messages=[
                {"role": "system", "content": "You are a medication advisor. Use the context to answer."},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: What is Metformin used for?"}
            ],
            temperature=0.1,
            max_tokens=200
        )

        answer = response.choices[0].message.content
        print(f"  SUCCESS: RAG pipeline working")
        print(f"  Question: What is Metformin used for?")
        print(f"  Answer: {answer[:150]}...")
        print()

except Exception as e:
    print(f"  FAILED: {str(e)}")
    print()
    exit(1)

print("=" * 60)
print("All Tests Passed!")
print("=" * 60)
print()
print("Run the app: streamlit run streamlit_app.py")
