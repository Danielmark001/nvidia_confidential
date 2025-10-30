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
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for layout
st.markdown("""
<style>
    .stApp {
        max-width: 100%;
    }

    .main {
        max-width: 900px;
        margin: 0 auto;
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

    [data-testid="stChatInput"] {
        position: sticky;
        bottom: 0;
        background-color: white;
        z-index: 100;
        padding: 1rem;
        border-top: 1px solid #ddd;
        margin-top: 1rem;
    }

    [data-testid="stChatInput"] input {
        background-color: transparent !important;
        border: 1px solid #999 !important;
        border-radius: 4px !important;
        padding: 0.6rem 0.8rem !important;
        font-size: 0.95rem !important;
        color: #333 !important;
        box-shadow: none !important;
    }

    [data-testid="stChatInput"] input::placeholder {
        color: #bbb !important;
    }

    [data-testid="stChatInput"] input:focus {
        border-color: #333 !important;
        outline: none !important;
        box-shadow: none !important;
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

    # Input section - always visible
    st.divider()

    # Voice settings - show first
    col1, col2 = st.columns([2, 1])
    with col1:
        if st.session_state.voice_enabled:
            audio_file = st.file_uploader(
                "Upload audio file",
                type=["wav", "mp3", "ogg", "m4a", "webm"],
                key="audio_uploader",
                help="Upload an audio file to transcribe and ask (ElevenLabs)"
            )
        else:
            audio_file = None
            st.info("Upload audio: ElevenLabs API not configured")
    with col2:
        if st.session_state.voice_enabled:
            enable_tts = st.checkbox("Voice reply", value=True, help="Get voice responses via ElevenLabs")
        else:
            enable_tts = False

    # Speech input button (works with browser, no API needed)
    st.markdown("""
<style>
    .speech-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.75rem 1.5rem !important;
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        cursor: pointer !important;
        box-shadow: 0 4px 6px rgba(102, 126, 234, 0.3) !important;
        transition: all 0.3s ease !important;
        width: 100%;
        margin: 0.5rem 0;
    }

    .speech-btn:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 12px rgba(102, 126, 234, 0.4) !important;
    }

    .speech-btn:active {
        transform: translateY(0) !important;
    }

    .speech-btn.listening {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%) !important;
        box-shadow: 0 4px 6px rgba(17, 153, 142, 0.3) !important;
        animation: pulse 1.5s infinite !important;
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.8; }
    }
</style>

<button id="speech-btn" class="speech-btn" onclick="window.startSpeech()">
    🎤 Speak
</button>

<script>
function initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
        console.error('Speech Recognition not supported in this browser');
        return;
    }

    window.recognition = new SpeechRecognition();
    window.recognition.continuous = false;
    window.recognition.interimResults = false;
    window.recognition.lang = 'en-US';

    window.startSpeech = function() {
        const btn = document.getElementById('speech-btn');
        btn.classList.add('listening');
        btn.textContent = '🎤 Listening...';

        window.recognition.start();
    };

    window.recognition.onresult = function(event) {
        const btn = document.getElementById('speech-btn');
        btn.classList.remove('listening');
        btn.textContent = '🎤 Speak';

        let transcript = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
            if (event.results[i].isFinal) {
                transcript += event.results[i][0].transcript;
            }
        }

        if (transcript) {
            const inputs = document.querySelectorAll('input[type="text"]');
            const chatInput = Array.from(inputs).find(input =>
                input.placeholder && input.placeholder.includes('medications')
            );

            if (chatInput) {
                chatInput.value = transcript;
                chatInput.dispatchEvent(new Event('input', { bubbles: true }));
                chatInput.dispatchEvent(new Event('change', { bubbles: true }));
                setTimeout(() => chatInput.focus(), 100);
            }
        }
    };

    window.recognition.onerror = function(event) {
        const btn = document.getElementById('speech-btn');
        btn.classList.remove('listening');
        btn.textContent = '🎤 Speak';
        console.error('Speech recognition error:', event.error);
    };

    window.recognition.onend = function() {
        const btn = document.getElementById('speech-btn');
        btn.classList.remove('listening');
        btn.textContent = '🎤 Speak';
    };
}

document.addEventListener('DOMContentLoaded', initSpeechRecognition);
if (document.readyState !== 'loading') {
    initSpeechRecognition();
}
</script>
""", unsafe_allow_html=True)

    # Text input - below speak button
    user_input = st.chat_input("Ask about medications or follow up with more questions...", key="text_input")

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
                        """, search_term=user_input)

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
                        system_prompt = """You are an expert medical information assistant specializing in medication guidance.

CRITICAL RULES FOR HIGH ACCURACY (Target F1≥0.80, Citation Precision≥0.90):
1. ONLY use information explicitly stated in the Knowledge Graph Data provided
2. NEVER infer, assume, or add information not present in the data
3. ALWAYS quote or paraphrase directly from the descriptions and indications
4. CITE the medication name you're referencing (e.g., "According to the data for [MedicationName]...")
5. If information is not in the data, state: "This information is not available in the knowledge graph"

Your role:
1. Extract and present facts directly from the knowledge graph
2. Use the exact terminology from the descriptions when possible
3. Explain mechanisms, indications, and classifications clearly
4. Add patient-friendly explanations in parentheses for medical terms
5. Structure answers with clear sections

Response structure (NO BOLD OR MARKDOWN FORMATTING):
- Medication: State the medication name from the data
- Primary Information: Quote/paraphrase key facts from description and indication
- Additional Details: Include mechanism or classification if available
- Citation: Source: Knowledge Graph - [MedicationName]
- Disclaimer: Note: This information is from the knowledge graph. Consult your healthcare provider for personalized medical advice.

Quality targets:
- F1-score ≥0.80 (match gold answers closely)
- Citation precision ≥0.90 (only cite valid knowledge graph nodes)
- Zero hallucination (no made-up facts)"""

                    elif response_style == "Concise (Brief)":
                        system_prompt = """You are a medication information assistant.

Guidelines:
- Provide brief, direct answers based on the knowledge graph data
- Use 2-3 sentences maximum
- Focus on the most important information only
- Avoid lengthy explanations unless specifically asked
- Still mention it's informational, not medical advice
- Do not use bold text, asterisks, or markdown formatting"""

                    else:
                        system_prompt = """You are an expert clinical pharmacologist providing technical medication information.

Guidelines:
- Use precise medical and pharmacological terminology
- Cite specific mechanisms, pathways, and drug classes
- Include relevant pharmacokinetics/pharmacodynamics when available
- Assume audience has medical background
- Reference the knowledge graph data with clinical accuracy
- Include appropriate clinical caveats
- Do not use bold text, asterisks, or markdown formatting"""

                    few_shot = """EXAMPLE:
KG Data: "Metformin - Description: Biguanide that decreases hepatic glucose production. Indication: Type 2 diabetes mellitus."
Question: "What is Metformin used for?"
Answer: "Metformin is indicated for type 2 diabetes mellitus. It decreases hepatic glucose production and improves glycemic control. Source: Knowledge Graph - Metformin"

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
