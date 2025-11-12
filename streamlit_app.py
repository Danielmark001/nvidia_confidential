"""
Medication Advisor with NVIDIA NIM + Neo4j + ElevenLabs Voice
Refactored version with improved code organization
"""

import streamlit as st
from dotenv import load_dotenv
import io

from src.ui.styles import apply_custom_styling
from src.ui.config_components import (
    get_secret,
    render_model_config,
    render_response_style_config,
    render_voice_config,
    render_system_status,
    render_header,
    render_welcome_info
)
from src.ui.ui_components import (
    render_avatar_selector,
    render_demo_mode_toggle,
    load_patient_scenarios,
    render_patient_selector,
    render_patient_card,
    render_voice_input
)
from src.services.medication_service import create_medication_service

load_dotenv()

st.set_page_config(
    page_title="Medication Advisor AI",
    page_icon="💊",
    layout="centered",
    initial_sidebar_state="expanded"
)

apply_custom_styling()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "voice_enabled" not in st.session_state:
    st.session_state.voice_enabled = False
if "selected_avatar" not in st.session_state:
    st.session_state.selected_avatar = "🤖"

with st.sidebar:
    st.markdown("""
    <div style="margin-bottom: 1.5rem;">
        <h2 style="margin: 0; color: #1f77b4; font-size: 1.5rem;">Model Settings</h2>
    </div>
    """, unsafe_allow_html=True)

    model_config = render_model_config()
    st.divider()

    with st.container():
        response_style = render_response_style_config()

    st.divider()

    with st.container():
        enable_tts = render_voice_config()

    st.divider()

    st.markdown("<h3 style='margin-top: 0; color: #667eea;'>✨ Features</h3>", unsafe_allow_html=True)
    avatar = render_avatar_selector()
    demo_mode = render_demo_mode_toggle()

    if demo_mode:
        st.markdown("---")
        try:
            scenarios = load_patient_scenarios()
            if scenarios:
                patient = render_patient_selector(scenarios)
                if patient:
                    render_patient_card(patient)
                    st.session_state.current_patient = patient
            else:
                st.info("No patient scenarios available")
        except Exception as e:
            st.warning(f"Error loading scenarios: {str(e)[:50]}")

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Reset Settings", use_container_width=True):
            st.rerun()

    with st.expander("Current Settings", expanded=False):
        st.code(f"""Model: {model_config['model'].split('/')[-1]}
Temperature: {model_config['temperature']}
Top P: {model_config['top_p']}
Max Tokens: {model_config['max_tokens']}
Style: {response_style}""", language="text")

main_col = st.container()

with main_col:
    render_header()

    with st.expander("System Status", expanded=False):
        render_system_status()

    if not st.session_state.messages:
        render_welcome_info()

    for message in st.session_state.messages:
        if message["role"] == "user":
            msg_avatar = "🧑"
        else:
            msg_avatar = st.session_state.get("selected_avatar", "💊")

        with st.chat_message(message["role"], avatar=msg_avatar):
            st.markdown(message["content"])

            if message["role"] == "assistant" and "audio" in message:
                st.audio(message["audio"], format="audio/mp3")

            if message["role"] == "assistant" and "sources" in message:
                with st.expander("Sources & Citations"):
                    for source in message["sources"]:
                        st.markdown(f"- {source}")

    if st.session_state.voice_enabled:
        render_voice_input()

        if st.session_state.get("audio_bytes") is not None:
            if st.button("🎯 Transcribe & Answer", use_container_width=True, key="transcribe_btn"):
                st.session_state.do_transcribe = True
                st.rerun()

    st.markdown("---")
    st.markdown("### Or Type Your Question")
    user_input = st.chat_input("How can I help you today?", key="text_input")

    if st.session_state.voice_enabled:
        audio_file = st.file_uploader(
            "Or upload an audio file",
            type=["wav", "mp3", "ogg", "m4a", "webm"],
            key="audio_uploader",
            label_visibility="collapsed"
        )
    else:
        audio_file = None

    if st.session_state.get("do_transcribe", False):
        with st.spinner("🎤 Transcribing your voice..."):
            try:
                from src.voice.elevenlabs_client import create_voice_client

                voice_client = create_voice_client()
                audio_file_obj = io.BytesIO(st.session_state.audio_bytes)
                transcribed_text = voice_client.speech_to_text(audio_file_obj)

                st.session_state.do_transcribe = False
                st.session_state.audio_bytes = None
                user_input = transcribed_text

            except Exception as e:
                st.error(f"Transcription error: {str(e)}")
                st.session_state.do_transcribe = False
                user_input = None

    if st.session_state.voice_enabled and audio_file is not None:
        with st.chat_message("user", avatar="🧑"):
            st.audio(audio_file)
            with st.spinner("Transcribing audio..."):
                try:
                    from src.voice.elevenlabs_client import create_voice_client

                    voice_client = create_voice_client()
                    audio_bytes = audio_file.read()
                    audio_file_obj = io.BytesIO(audio_bytes)
                    transcribed_text = voice_client.speech_to_text(audio_file_obj)

                    st.success(f"Transcribed: {transcribed_text}")
                    user_input = transcribed_text

                except Exception as e:
                    st.error(f"Transcription error: {str(e)}")
                    user_input = None

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})

        with st.chat_message("user", avatar="🧑"):
            st.markdown(user_input)

        with st.chat_message("assistant", avatar="💊"):
            try:
                nvidia_key = get_secret("NVIDIA_API_KEY")
                neo4j_uri = get_secret("NEO4J_URI")
                neo4j_user = get_secret("NEO4J_USERNAME")
                neo4j_pass = get_secret("NEO4J_PASSWORD")

                if not all([nvidia_key, neo4j_uri, neo4j_user, neo4j_pass]):
                    st.error("Missing configuration. Please check your credentials.")
                    st.stop()

                with st.spinner("Processing your question..."):
                    service = create_medication_service(
                        nvidia_api_key=nvidia_key,
                        neo4j_uri=neo4j_uri,
                        neo4j_user=neo4j_user,
                        neo4j_pass=neo4j_pass
                    )

                    patient_context = st.session_state.get("current_patient") if demo_mode else None

                    result = service.process_query(
                        user_query=user_input,
                        model=model_config["model"],
                        temperature=model_config["temperature"],
                        top_p=model_config["top_p"],
                        max_tokens=model_config["max_tokens"],
                        response_style=response_style,
                        patient_context=patient_context
                    )

                st.markdown(result["answer"])

                audio_data = None
                if st.session_state.voice_enabled and enable_tts:
                    with st.spinner("Generating voice response..."):
                        try:
                            from src.voice.elevenlabs_client import create_voice_client

                            voice_client = create_voice_client()
                            audio_bytes = voice_client.text_to_speech(result["answer"])
                            audio_data = audio_bytes
                            st.audio(audio_bytes, format="audio/mp3")

                        except Exception as e:
                            st.warning(f"Voice generation unavailable: {str(e)}")

                with st.expander("Knowledge Graph Context"):
                    st.text(result["context"])

                message_data = {
                    "role": "assistant",
                    "content": result["answer"]
                }
                if audio_data:
                    message_data["audio"] = audio_data

                if result["medications"]:
                    message_data["medications"] = result["medications"]

                st.session_state.messages.append(message_data)

            except Exception as e:
                error_msg = f"Error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })

    st.markdown("---")
    st.markdown("""
    <div class="footer-text">
        Informational purposes only. Consult healthcare professionals for medical advice.
    </div>
    """, unsafe_allow_html=True)
