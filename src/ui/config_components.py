"""UI components for model configuration and settings."""

import streamlit as st
from typing import Dict


def get_secret(key: str, default: str = "") -> str:
    """Get secret from Streamlit secrets or environment variables."""
    import os

    try:
        if key in st.secrets:
            return st.secrets[key]
    except:
        pass

    env_val = os.getenv(key)
    if env_val:
        return env_val

    return default


def render_model_config() -> Dict:
    """Render model configuration sidebar section."""
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

    return {
        "model": model_choice,
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": max_tokens
    }


def render_response_style_config() -> str:
    """Render response style configuration."""
    st.markdown("<h3 style='margin-top: 0; color: #333;'>Response Format</h3>", unsafe_allow_html=True)

    response_style = st.radio(
        "Style",
        options=["Detailed (Structured)", "Concise (Brief)", "Expert (Technical)"],
        index=0,
        help="Choose how responses are formatted"
    )

    return response_style


def render_voice_config() -> bool:
    """Render voice configuration."""
    st.markdown("<h3 style='margin-top: 0; color: #333;'>Voice Options</h3>", unsafe_allow_html=True)

    if st.session_state.voice_enabled:
        enable_tts = st.checkbox("Voice reply", value=True, help="Get voice responses via ElevenLabs", key="sidebar_tts")
    else:
        enable_tts = False
        st.info("ElevenLabs API not configured")

    return enable_tts


def render_system_status():
    """Render system status badges."""
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


def render_header():
    """Render application header."""
    st.markdown("""
    <div class="main-header">
        <h1>Medication Advisor AI</h1>
        <p style="color: #666; margin-top: 0.5rem; font-size: 0.9rem;">
            Powered by NVIDIA NIM (Llama 3.1 70B) | Neo4j Knowledge Graph | ElevenLabs Voice
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_welcome_info():
    """Render welcome info box."""
    st.markdown("""
    <div class="info-box">
        <strong>How to use:</strong><br>
        • Type a question about medications in the input box<br>
        • Or click the "Speak" button to ask directly by voice<br>
        • Upload an audio file for transcription (if voice is enabled)<br>
        • Get answers from our knowledge graph of 15,236+ medications
    </div>
    """, unsafe_allow_html=True)
