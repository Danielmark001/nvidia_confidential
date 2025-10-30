# Medication Advisor AI with NVIDIA NIMs

Streamlit chatbot with ElevenLabs voice I/O, Neo4j Knowledge Graph, and NVIDIA NIM-served LLM

**📖 [See Comprehensive Documentation →](docs/README.md)**

## Summary

**Why we need this project** Patients frequently misinterpret or forget medication instructions after leaving hospital, leading to avoidable readmissions and costs. A conversational assistant that can answer questions in plain language, grounded by a knowledge graph and offers an accessible safety net.

**What the system does** It captures spoken questions, converts them to text with ElevenLabs Scribe, retrieves facts from a Neo4j knowledge graph built from discharge notes and DrugBank data, drafts an answer with a Llama-3 model running on NVIDIA Inference Microservices (NIM), and replies using ElevenLabs TTS.

**What is evaluated** We measure answer correctness (F1-score), citation precision to the KG, and performance drops in an ablation study (KG-only vs. LLM-only). Speech metrics are out of scope.

**How it contributes (and where it leads)** The finished 3-month prototype doubles as a demo for healthcare/AI stakeholders and as teaching material. Week 12 outputs include a ready-to-show demo video plus a one-hour workshop with slides and a hands-on lab showcasing how to run LLMs on NIM and query knowledge graphs with LangChain. In the next phase, the pipeline can be extended toward drug-discovery use cases: e.g., mapping similar chemical entities, suggesting repurposing candidates, or integrating cheminformatics graphs by leveraging the same NIM/Neo4j/LLM stack. Week 12 outputs include a ready-to-show demo video plus a one-hour workshop with slides and a hands-on lab showcasing how to run LLMs on NIM and LangChain.

---

## 1. Why build this?

Patients often leave hospital uncertain about their new medicines. A friendly assistant that listens to their spoken questions, reasons over a small knowledge graph built from the discharge summary, and talks back with clear instructions can cut confusion and errors.

---

## 2. Project Goal

Build a **Streamlit web app** that:

1. Captures the patient's speech via microphone.
2. Uses **ElevenLabs Scribe** (STT) to convert speech → text.
3. Looks up answers in a **Neo4j knowledge graph** populated from real discharge notes and DrugBank interactions.
4. Calls a **Llama-3-Instruct model** hosted through the **NVIDIA NIM API (NVIDIA Inference Microservices)** to draft a natural-language response citing KG facts.
5. **Delivers educational value** by producing a workshop slide deck and hands-on lab that teach how to combine NIM-hosted LLMs with knowledge-graph retrieval.

---

## 3. Core Components

| Layer | Tool / Service |
|-------|----------------|
| **Speech-to-Text** | ElevenLabs Scribe REST endpoint (supports 99 languages, word-level timestamps). |
| **Text-to-Speech** | ElevenLabs TTS with optional cloned caregiver voice for familiarity. |
| **Knowledge Graph** | Neo4j Desktop (or Aura Free). Nodes: Patient, Medication, Dose, Schedule, Interaction, Advice. Edges: TAKES, CONTRAINDICATES, etc. |
| **LLM** | Llama-3-Instruct served by an NVIDIA LLM NIM container (pull from NGC, REST API). |
| **Orchestration** | LangChain Cypher QA chain (question → Cypher → KG facts → NIM LLM → answer + citation). |
| **UI** | Streamlit (`st.chat_input()`, `st.audio()`). |

### System Overview Diagram

```
Patient Microphone (Streamlit UI)
        ↓
ElevenLabs Scribe (Speech-to-Text)
        ↓
        speech text
        ↓
    LangChain ← ─ ─ ─ ─ ─ ─ ─ ─ Cypher query
    Orchestrator           ↓
        ↓               Neo4j Knowledge Graph
        facts ← ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ↓
        ↓                      facts
    Llama-3 (NIM)
        ↓
    draft answer
        ↓
ElevenLabs TTS (Voice Clean)
        ↓
Audio Output (Streamlit UI)
```

---

## 4. Public Datasets

*[Note to students: this overview is surveyed by AI, please do check through in case of erroneous information]*

Below are five datasets that can fuel your knowledge graph. Each row tells you what it contains, roughly how big it is, and any quick steps to download. **Start with the i2b2 set** (smallest friction) and layer in others as you iterate.

| Dataset | What's inside? | Quick access steps | Approx. size |
|---------|----------------|--------------------|-------------|
| **i2b2 2014 Discharge Summaries** | 1 300 anonymised discharge summaries in plain text with section labels. Perfect starter corpus to practise parsing medications & doses. | Request access on the n2c2 portal, sign the data-use agreement (usually granted within 24-48 h). | Zip = 95 MB |
| **SyntheticMass FHIR** | Fully synthetic patient records in FHIR JSON—no PII concerns. Good for learning FHIR structures and testing ETL scripts. | Hit the open REST endpoint (https://syntheticmass.mitre.org/fhir/Patient) or download a bulk export. | < 50 MB |
| **MIMIC-IV Notes (Discharge slice)** | Real ICU discharge notes with rich clinical detail. Adds realism once your pipeline works on i2b2. | PhysioNet account → CITI "Data or Specimens Only Research" module → sign DUA → download CSV. | Discharge slice = 1.5 GB |
| **DrugBank Open** | Structured drug metadata—names, interactions, dosing forms—ideal for enriching the KG with interaction facts. | Create a free DrugBank account, click "Download TSV/XML". | ≈ 40 MB compressed |
| **DDI 2013 Corpus (optional)** | Sentence-level annotations of drug–drug interactions, handy for fine-tuning relation extraction models. | Direct download from the project page—no signup. | ≈ 22 MB |

---

## Recommended first steps

1. Download **i2b2 2014** and load five notes into Neo4j to verify your schema.
2. Add **DrugBank** nodes for each medication that appears.
3. Once the pipeline is stable, scale up with the **MIMIC-IV discharge slice** for more variety.

---

## 5. Development Roadmap (12 Weeks)

| Weeks | Key Tasks |
|-------|-----------|
| **1–2** | Download sample discharge notes and DrugBank TSV; parse medications and doses. |
| **3–4** | Write Python ETL to extract triples and load them into Neo4j. |
| **5–6** | Spin up a Llama-3 NIM container on a local GPU or Colab; test with simple prompts. |
| **7–8** | Build the LangChain Cypher QA chain: question → MATCH → KG facts → answer. |
| **9–10** | Integrate ElevenLabs Scribe STT and ElevenLabs TTS in Streamlit; finalise the chat UI. |
| **11** | Run user testing with 20 scripted questions; log answers and citations. |
| **12** | Analyse metrics, polish the UI, create demo video & short report, and draft workshop slide deck + 1-hour hands-on lab guide. |

---

## 6. Evaluation Plan (focus on answer quality)

### Evaluation Plan (focus on answer quality). Evaluation Plan (focus on answer quality)

| Aspect | Metric | Goal |
|--------|--------|------|
| **Answer correctness** | *F1-score* against gold answers | ≥ 0.80 |
| **Citation quality** | *Graph Precision* (valid citations ÷ total) | ≥ 0.90 |
| **Ablation study impact** | Δ *F1* when KG or LLM removed | Report & discuss |

### Step-by-Step Evaluation Procedure

#### 1. Create the Question Set
- Sample 50 real questions from MIMIC-IV discharge notes (e.g., timing, dosage, interactions).
- Two annotators rewrite into patient-friendly wording.

#### 2. Annotate Gold Answers
- Annotators mark the exact sentence(s) in the discharge note or DrugBank entry that fully answer each question.
- Resolve conflicts with a third reviewer; store IDs of supporting KG nodes/edges.

#### 3. Run the System
- Use a Python script (example notebook: https://github.com/langchain-ai/graph-qa-examples) to feed each question via the Streamlit backend, save JSON: `{question, answer, cited_nodes}`.

#### 4. Compute Answer F1
- Treat gold text as reference, system answer as prediction.
- Use scikit-learn's precision_recall_fscore_support (doc: https://scikit-learn.org/stable/modules/generated/sklearn.metrics.precision_recall_fscore_support.html) to calculate token-level F1.

#### 5. Check Citation Precision
- For every cited KG node/edge, verify it is among the gold support set (simple set intersection).
- `precision = |valid| / |cited|` per answer, then average.

#### 6. Ablation Runs
- **Variant A** – template answer: bypass LLM, fill in pre-written dosage strings from KG.
- **Variant B** – LLM without KG: feed question directly to LLM.
- Report F1 for both and discuss drops vs. full system.

#### 7. Report & Visualise
- Include a confusion matrix for common dosage/unit errors.
- Show bar chart of citation precision by question type (dosage vs. interaction).

**Guide references**
- "Best Practices for Creating QA Datasets" – ACL 2023 tutorial (https://qa-best-practices.acl2023.org)
- Neo4j Cipher cheatsheet – https://neo4j.com/docs/cypher_refcard/current/
- LangChain KG QA example – https://python.langchain.com/docs/use_cases/graph_qa
- Scikit-learn metrics guide – https://scikit-learn.org/stable/modules/model_evaluation.html

*No speech-specific metrics are needed—the evaluation focuses purely on text-answer quality and citation fidelity.*

---

## 7. Future Work: Drug-Discovery Extension

After the 12-week milestone, the project can evolve beyond discharge guidance by: 1. **Adding chemistry KGs** such as ChEMBL or PubChem compounds. 2. **Integrating similarity search** (Tanimoto, fingerprint vectors) via Python RDKit and linking compounds to DrugBank records. 3. **Fine-tuning the LLM** with medicinal-chemistry Q&A to suggest potential drug-repurposing leads. 4. **Demonstrating a new workflow**: "Given these adverse-event patterns, propose safer alternative drugs."

These steps reuse the same NIM-hosted Llama-3 endpoint and Neo4j schema, illustrating how the architecture scales from clinical counselling to early-stage drug-discovery insights.

---

## 8. Helpful Links

- **ElevenLabs API Docs (Scribe & TTS)** – https://docs.elevenlabs.io
- **LangChain Knowledge-Graph QA** – https://python.langchain.com/docs/use_cases/graph_qa
- **Neo4j Getting Started** – https://neo4j.com/developer/get-started/
- **NVIDIA NIM Quick Start** – https://developer.nvidia.com/blog/getting-started-nims/
- **Streamlit Audio Components** – https://docs.streamlit.io/library/api-reference/media/st.audio
- **scikit-learn Evaluation Examples** – https://scikit-learn.org/stable/auto_examples/model_selection/plot_confusion_matrix.html

---

## Acronym Cheat-Sheet

| Acronym | Meaning |
|---------|---------|
| **i2b2** | *Informatics for Integrating Biology & the Bedside* – a clinical NLP challenge series that released the 2014 discharge summary dataset. |
| **FHIR** | *Fast Healthcare Interoperability Resources* – HL7's standard for exchanging healthcare data in JSON / XML format. |
| **ETL** | *Extract-Transform-Load* – the pipeline for moving raw text into the Neo4j knowledge graph. |
| **STT / TTS** | *Speech-to-Text / Text-to-Speech*. |
| **LLM** | *Large Language Model* (e.g., Llama-3). |
| **NIM** | *NVIDIA Inference Microservices* – a family of pre-built, GPU-accelerated model servers. (Not to be confused with "NeΜo microservices," which focus on training and customization.) |
| **ICU** | *Intensive Care Unit* – hospital ward type referenced in MIMIC data. |
| **KG** | *Knowledge Graph*. |
