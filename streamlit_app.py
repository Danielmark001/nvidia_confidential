"""
Medication Advisor with NVIDIA NIM + Neo4j + ElevenLabs Voice
Barebones implementation with voice input/output support
"""

import streamlit as st
from dotenv import load_dotenv
import os
import io

load_dotenv()

def get_secret(key: str, default: str = "") -> str:
    # Try Streamlit secrets first
    try:
        if key in st.secrets:
            return st.secrets[key]
    except:
        pass

    # Try environment variable
    env_val = os.getenv(key)
    if env_val:
        return env_val

    return default

st.set_page_config(
    page_title="Medication Advisor AI - Updated",
    page_icon="💊",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Custom CSS for layout
st.markdown("""
<style>
    .stApp {
        max-width: 100%;
    }

    .main {
        max-width: 1000px;
        margin: 0 auto;
    }

    [data-testid="stSidebar"] {
        min-width: 350px !important;
        max-width: 350px !important;
    }

    [data-testid="stSidebar"] > div:first-child {
        width: 350px !important;
    }

    .main-header {
        text-align: center;
        padding: 1rem 0 2rem 0;
        border-bottom: 2px solid #e8eef7;
        margin-bottom: 2rem;
    }

    .main-header h1 {
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }

    .status-badge {
        display: inline-block;
        padding: 0.35rem 0.85rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
        margin: 0.25rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .status-success {
        background-color: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }

    .status-error {
        background-color: #f8d7da;
        color: #721c24;
        border: 1px solid #f5c6cb;
    }

    .info-box {
        background: linear-gradient(135deg, #f0f4ff 0%, #f8fbff 100%);
        border-left: 4px solid #1f77b4;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(31, 119, 180, 0.08);
    }

    [data-testid="stChatMessageContent"] {
        padding: 1rem;
        border-radius: 8px;
    }

    .main > div:last-child {
        padding-bottom: 150px;
    }

    /* Input container fixed at bottom */
    .input-wrapper {
        position: fixed !important;
        bottom: 0 !important;
        left: 50% !important;
        transform: translateX(-50%) !important;
        width: 100% !important;
        max-width: 800px !important;
        background-color: white !important;
        z-index: 1000 !important;
        padding: 1.5rem 2rem !important;
        box-shadow: 0 -2px 20px rgba(0, 0, 0, 0.08) !important;
    }

    [data-testid="stChatInput"] {
        position: fixed !important;
        bottom: 0 !important;
        left: 350px !important;
        width: calc(100% - 350px) !important;
        max-width: 750px !important;
        background-color: white !important;
        z-index: 1000 !important;
        padding: 1.5rem 2rem 2rem 2rem !important;
        box-shadow: 0 -2px 20px rgba(0, 0, 0, 0.08) !important;
        margin: 0 !important;
        margin-left: 4rem !important;
    }

    [data-testid="stChatInput"] input {
        background-color: #ffffff !important;
        border: 5px solid #667eea !important;
        border-radius: 50px !important;
        padding: 2rem 3rem !important;
        font-size: 1.4rem !important;
        color: #000000 !important;
        font-weight: 700 !important;
        box-shadow: 0 6px 24px rgba(102, 126, 234, 0.25) !important;
        transition: all 0.3s ease !important;
        min-height: 70px !important;
    }

    [data-testid="stChatInput"] input:focus {
        border-color: #667eea !important;
        background-color: white !important;
        outline: none !important;
        box-shadow: 0 8px 24px rgba(102, 126, 234, 0.35) !important;
        transform: translateY(-3px) !important;
    }

    /* File uploader styling - compact and user-friendly */
    [data-testid="stFileUploader"] {
        position: fixed !important;
        bottom: 2rem !important;
        right: 2rem !important;
        z-index: 1001 !important;
    }

    [data-testid="stFileUploader"] section {
        padding: 0.8rem 1.2rem !important;
        border: 2px solid #667eea !important;
        border-radius: 24px !important;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        transition: all 0.3s ease !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: 0 3px 10px rgba(102, 126, 234, 0.3) !important;
    }

    [data-testid="stFileUploader"] section:hover {
        background: linear-gradient(135deg, #5568d3 0%, #6a4091 100%) !important;
        box-shadow: 0 5px 18px rgba(102, 126, 234, 0.45) !important;
        transform: translateY(-2px) !important;
    }

    [data-testid="stFileUploader"] button {
        font-size: 0.95rem !important;
        padding: 0.2rem 0.5rem !important;
        background: transparent !important;
        border: none !important;
        transition: all 0.3s !important;
        cursor: pointer !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        letter-spacing: 0.3px !important;
    }

    [data-testid="stFileUploader"] button:hover {
        background: transparent !important;
        color: #ffffff !important;
    }

    [data-testid="stFileUploader"] button span {
        display: block !important;
        color: #ffffff !important;
    }

    [data-testid="stFileUploader"] button * {
        color: #ffffff !important;
    }

    [data-testid="stFileUploader"] button::before {
        content: "" !important;
        display: none !important;
    }

    [data-testid="stFileUploader"] label {
        display: none !important;
    }

    /* Style drag and drop text to be white */
    [data-testid="stFileUploader"] small {
        color: #ffffff !important;
        font-size: 0.8rem !important;
    }

    [data-testid="stFileUploader"] [data-testid="stMarkdownContainer"] {
        color: #ffffff !important;
    }

    [data-testid="stFileUploader"] p {
        color: #ffffff !important;
    }

    [data-testid="stFileUploader"] div {
        color: #ffffff !important;
    }

    [data-testid="stChatInput"] input::placeholder {
        color: #95a5a6 !important;
        font-weight: 400 !important;
    }

    [data-testid="stHorizontalBlock"] {
        gap: 0.5rem;
    }

    .stDivider {
        margin: 1.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "voice_enabled" not in st.session_state:
    st.session_state.voice_enabled = False

# Sidebar - Model Configuration
with st.sidebar:
    st.markdown("""
    <div style="margin-bottom: 1.5rem;">
        <h2 style="margin: 0; color: #1f77b4; font-size: 1.5rem;">Model Settings</h2>
    </div>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown("<h3 style='margin-top: 0; color: #333;'>LLM Configuration</h3>", unsafe_allow_html=True)

        model_choice = st.selectbox(
            "Model",
            options=[
                "meta/llama-3.3-70b-instruct",
                "meta/llama-3.1-70b-instruct",
                "nvidia/llama-3.1-nemotron-70b-instruct",
                "mistralai/mixtral-8x22b-instruct-v0.1"
            ],
            index=0,
            help="Choose the LLM model. Llama 3.3 recommended for accuracy."
        )

        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=0.05,
            step=0.05,
            help="Lower = more focused/accurate, Higher = more creative"
        )

        top_p = st.slider(
            "Top P",
            min_value=0.0,
            max_value=1.0,
            value=0.95,
            step=0.05,
            help="Nucleus sampling threshold. 0.95 is recommended"
        )

        max_tokens = st.slider(
            "Max Tokens",
            min_value=128,
            max_value=2048,
            value=768,
            step=128,
            help="Maximum response length. Higher = more detailed"
        )

    st.divider()

    with st.container():
        st.markdown("<h3 style='margin-top: 0; color: #333;'>Response Format</h3>", unsafe_allow_html=True)

        response_style = st.radio(
            "Style",
            options=["Detailed (Structured)", "Concise (Brief)", "Expert (Technical)"],
            index=0,
            help="Choose how responses are formatted"
        )

    st.divider()

    with st.container():
        st.markdown("<h3 style='margin-top: 0; color: #333;'>Voice Options</h3>", unsafe_allow_html=True)

        if st.session_state.voice_enabled:
            enable_tts = st.checkbox("Voice reply", value=True, help="Get voice responses via ElevenLabs", key="sidebar_tts")
        else:
            enable_tts = False
            st.info("ElevenLabs API not configured")

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Reset Settings", use_container_width=True):
            st.rerun()

    with st.expander("Current Settings", expanded=False):
        st.code(f"""Model: {model_choice.split('/')[-1]}
Temperature: {temperature}
Top P: {top_p}
Max Tokens: {max_tokens}
Style: {response_style}""", language="text")

# Main content wrapper with centering
main_col = st.container()

with main_col:
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>Medication Advisor AI</h1>
        <p style="color: #666; margin-top: 0.5rem; font-size: 0.9rem;">
            Powered by NVIDIA NIM (Llama 3.1 70B) | Neo4j Knowledge Graph | ElevenLabs Voice
        </p>
    </div>
    """, unsafe_allow_html=True)

    # System status check
    with st.expander("System Status", expanded=False):
        col1, col2, col3 = st.columns(3)

        with col1:
            nvidia_key = get_secret("NVIDIA_API_KEY", "")
            if nvidia_key:
                st.markdown('<span class="status-badge status-success">✓ NVIDIA NIM</span>', unsafe_allow_html=True)
            else:
                st.markdown('<span class="status-badge status-error">✗ NVIDIA NIM</span>', unsafe_allow_html=True)

        with col2:
            neo4j_uri = get_secret("NEO4J_URI", "")
            if neo4j_uri:
                st.markdown('<span class="status-badge status-success">✓ Neo4j</span>', unsafe_allow_html=True)
            else:
                st.markdown('<span class="status-badge status-error">✗ Neo4j</span>', unsafe_allow_html=True)

        with col3:
            elevenlabs_key = get_secret("ELEVENLABS_API_KEY", "")
            if elevenlabs_key:
                st.markdown('<span class="status-badge status-success">✓ ElevenLabs</span>', unsafe_allow_html=True)
                st.session_state.voice_enabled = True
            else:
                st.markdown('<span class="status-badge status-error">✗ ElevenLabs</span>', unsafe_allow_html=True)
                st.session_state.voice_enabled = False

    # Quick info
    if not st.session_state.messages:
        st.markdown("""
        <div class="info-box">
            <strong>How to use:</strong><br>
            • Type a question about medications in the input box<br>
            • Or click the "Speak" button to ask directly by voice<br>
            • Upload an audio file for transcription (if voice is enabled)<br>
            • Get answers from our knowledge graph of 15,236+ medications
        </div>
        """, unsafe_allow_html=True)

    # Display chat messages
    for message in st.session_state.messages:
        avatar = "🧑" if message["role"] == "user" else "💊"
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

            # Show audio player if response has audio
            if message["role"] == "assistant" and "audio" in message:
                st.audio(message["audio"], format="audio/mp3")

    # Audio upload (will be positioned to the left of text input with CSS)
    if st.session_state.voice_enabled:
        audio_file = st.file_uploader(
            "Upload Audio",
            type=["wav", "mp3", "ogg", "m4a", "webm"],
            key="audio_uploader",
            help="Upload audio file to transcribe",
            label_visibility="collapsed"
        )
    else:
        audio_file = None

    # Text input
    user_input = st.chat_input("How can I help you today?", key="text_input")

    # Process audio input
    if st.session_state.voice_enabled and audio_file is not None:
        with st.chat_message("user", avatar="🧑"):
            st.audio(audio_file)
            with st.spinner("Transcribing audio..."):
                try:
                    from src.voice.elevenlabs_client import create_voice_client

                    voice_client = create_voice_client()

                    # Read audio bytes
                    audio_bytes = audio_file.read()
                    audio_file_obj = io.BytesIO(audio_bytes)

                    # Transcribe
                    transcribed_text = voice_client.speech_to_text(audio_file_obj)

                    st.success(f"Transcribed: {transcribed_text}")
                    user_input = transcribed_text

                except Exception as e:
                    st.error(f"Transcription error: {str(e)}")
                    user_input = None

    # Process text input (from typing or transcription)
    if user_input:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})

        with st.chat_message("user", avatar="🧑"):
            st.markdown(user_input)

        # Generate response
        with st.chat_message("assistant", avatar="💊"):
            try:
                # Step 0: Generate optimal search query using LLM
                with st.spinner("Understanding your question..."):
                    from openai import OpenAI

                    client = OpenAI(
                        base_url="https://integrate.api.nvidia.com/v1",
                        api_key=get_secret("NVIDIA_API_KEY")
                    )

                    extraction_response = client.chat.completions.create(
                        model=model_choice,
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
                                "content": user_input
                            }
                        ],
                        temperature=0.0,
                        max_tokens=50
                    )

                    search_terms = extraction_response.choices[0].message.content.strip()

                # Step 1: Query Neo4j
                with st.spinner("Searching medication database..."):
                    from neo4j import GraphDatabase

                    neo4j_uri = get_secret("NEO4J_URI")
                    neo4j_user = get_secret("NEO4J_USERNAME")
                    neo4j_pass = get_secret("NEO4J_PASSWORD")

                    if not neo4j_uri or not neo4j_user or not neo4j_pass:
                        st.error("Neo4j credentials not configured. Please check your .streamlit/secrets.toml file.")
                        st.stop()

                    driver = GraphDatabase.driver(
                        neo4j_uri,
                        auth=(neo4j_user, neo4j_pass)
                    )

                    with driver.session() as session:
                        result = session.run("""
                            CALL db.index.fulltext.queryNodes('medication_fulltext', $search_term)
                            YIELD node, score
                            RETURN node.name as name,
                                   node.description as description,
                                   node.indication as indication
                            LIMIT 3
                        """, search_term=search_terms)

                        kg_results = []
                        for record in result:
                            kg_results.append({
                                "name": record["name"],
                                "description": record["description"][:500] if record["description"] else "",
                                "indication": record["indication"][:500] if record["indication"] else ""
                            })

                    driver.close()

                # Prepare context
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

                # Step 2: Call NVIDIA NIM
                with st.spinner("Generating response with AI..."):
                    from openai import OpenAI

                    client = OpenAI(
                        base_url="https://integrate.api.nvidia.com/v1",
                        api_key=get_secret("NVIDIA_API_KEY")
                    )

                    # Adjust system prompt based on response style
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

                    few_shot = """EXAMPLE:
KG Data: "Metformin - Description: Biguanide that decreases hepatic glucose production. Indication: Type 2 diabetes mellitus."
Question: "What is Metformin used for?"
Answer: "Metformin is used to treat type 2 diabetes mellitus. It works by decreasing the amount of glucose your liver produces, which helps improve blood sugar control. As a biguanide medication, it's particularly effective for managing glycemic levels in diabetic patients. Remember to consult your healthcare provider for personalized advice about this medication."

---"""

                    user_message = f"""{few_shot}

Knowledge Graph Data (ONLY SOURCE OF TRUTH):
{context}

Patient Question: {user_input}

Answer following the EXAMPLE format. Use ONLY the data provided above."""

                    messages = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ]

                    response = client.chat.completions.create(
                        model=model_choice,
                        messages=messages,
                        temperature=temperature,
                        top_p=top_p,
                        max_tokens=max_tokens
                    )

                    answer = response.choices[0].message.content

                # Display text response
                st.markdown(answer)

                # Generate audio if enabled
                audio_data = None
                if st.session_state.voice_enabled and enable_tts:
                    with st.spinner("Generating voice response..."):
                        try:
                            from src.voice.elevenlabs_client import create_voice_client

                            voice_client = create_voice_client()
                            audio_bytes = voice_client.text_to_speech(answer)
                            audio_data = audio_bytes

                            st.audio(audio_bytes, format="audio/mp3")

                        except Exception as e:
                            st.warning(f"Voice generation unavailable: {str(e)}")

                # Show KG source
                with st.expander("Knowledge Graph Context"):
                    st.text(context)

                # Save to history
                message_data = {
                    "role": "assistant",
                    "content": answer
                }
                if audio_data:
                    message_data["audio"] = audio_data

                st.session_state.messages.append(message_data)

                # Scroll to input box
                st.markdown("""
                <script>
                    setTimeout(() => {
                        const inputBox = document.querySelector('[data-testid="stChatInput"]');
                        if (inputBox) {
                            inputBox.scrollIntoView({behavior: 'smooth', block: 'end'});
                        }
                    }, 100);
                </script>
                """, unsafe_allow_html=True)

            except Exception as e:
                error_msg = f"Error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })

                # Scroll to input box
                st.markdown("""
                <script>
                    setTimeout(() => {
                        const inputBox = document.querySelector('[data-testid="stChatInput"]');
                        if (inputBox) {
                            inputBox.scrollIntoView({behavior: 'smooth', block: 'end'});
                        }
                    }, 100);
                </script>
                """, unsafe_allow_html=True)

    # Footer
    st.markdown("---")
    st.markdown("""
    <div class="footer-text">
        Informational purposes only. Consult healthcare professionals for medical advice.
    </div>
    """, unsafe_allow_html=True)
