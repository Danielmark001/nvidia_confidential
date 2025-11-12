"""Reusable UI components for the Streamlit app."""

import streamlit as st
from typing import Dict, List, Optional
import json
import io


def render_avatar_selector():
    """Render avatar selection in sidebar."""
    avatar_options = {"Doctor": "🏥", "Medical Bot": "🤖", "Assistant": "💊"}
    selected = st.sidebar.selectbox("AI Advisor Avatar", list(avatar_options.keys()), index=1)
    avatar = avatar_options.get(selected, "🤖")
    st.session_state.selected_avatar = avatar
    return avatar


def render_demo_mode_toggle():
    """Render demo mode toggle in sidebar."""
    return st.sidebar.toggle("Enable Demo Mode", value=False)


def load_patient_scenarios():
    """Load patient scenarios from JSON file."""
    import os
    scenario_file = "data/scenarios/patient_scenarios.json"
    if os.path.exists(scenario_file):
        with open(scenario_file, 'r') as f:
            return json.load(f)
    return []


def render_patient_selector(scenarios):
    """Render patient scenario selector."""
    if not scenarios:
        return None
    patient_names = [f"{s['name']} ({s['age']}y)" for s in scenarios]
    selected_idx = st.sidebar.selectbox("Select Patient", range(len(scenarios)), format_func=lambda i: patient_names[i])
    return scenarios[selected_idx]


def render_patient_card(patient):
    """Render patient information card."""
    with st.sidebar.container():
        st.markdown("### Patient Profile")
        st.markdown(f"**Name:** {patient['name']}")
        st.markdown(f"**Age:** {patient['age']}")
        st.markdown(f"**Diagnoses:** {', '.join(patient['diagnoses'])}")


def render_medications_list(medications: List[Dict]):
    """Render list of medications in a readable format."""
    st.subheader("Current Medications")

    for i, med in enumerate(medications, 1):
        with st.expander(f"{i}. {med.get('name', 'Unknown')} - {med.get('dosage', 'N/A')}"):
            col1, col2 = st.columns(2)

            with col1:
                st.write(f"**Dosage:** {med.get('dosage', 'N/A')}")
                st.write(f"**Route:** {med.get('route', 'N/A')}")

            with col2:
                st.write(f"**Frequency:** {med.get('frequency', 'N/A')}")
                st.write(f"**Indication:** {med.get('indication', 'N/A')}")

            st.write(f"**Instructions:** {med.get('instructions', 'N/A')}")


def render_diagnoses_list(diagnoses: List[Dict]):
    """Render list of diagnoses."""
    st.subheader("Diagnoses")

    for diag in diagnoses:
        st.write(f"- **{diag.get('name', 'Unknown')}** (Code: {diag.get('code', 'N/A')})")


def render_graph_visualization(nodes: List[Dict], edges: List[Dict], height: int = 500):
    """
    Render knowledge graph visualization using streamlit-agraph.

    Args:
        nodes: List of node dictionaries
        edges: List of edge dictionaries
        height: Height of the graph container
    """
    try:
        from streamlit_agraph import agraph, Config

        config = Config(
            directed=True,
            height=height,
            nodeHighlightBehavior=True,
            highlightColor="#667eea",
            physics=True,
            directed_particle_ratio=0.05
        )

        agraph(
            nodes=nodes,
            edges=edges,
            config=config
        )

    except ImportError:
        st.warning(
            "Graph visualization requires streamlit-agraph. "
            "Install with: `pip install streamlit-agraph`"
        )
    except Exception as e:
        st.error(f"Error rendering graph: {str(e)[:100]}")


def render_voice_input():
    """Render voice input using audio-recorder-streamlit component."""
    try:
        from audio_recorder_streamlit import audio_recorder
        import numpy as np
        import soundfile as sf

        st.markdown("### 🎤 Record Your Question")
        st.info("Click the microphone button below to start recording. Click again to stop.")

        audio_bytes = audio_recorder(
            text="Click to record",
            recording_color="#ff4444",
            neutral_color="#667eea",
            icon_name="microphone",
            icon_size="2x",
            key="audio_recorder"
        )

        if audio_bytes:
            try:
                # Don't process the audio - use it directly for better quality
                # Store raw audio bytes for transcription
                st.session_state.audio_bytes = audio_bytes

                # Calculate duration for display
                audio_data = np.frombuffer(audio_bytes, dtype=np.int16)
                # audio-recorder-streamlit uses 44100 Hz sample rate
                duration = len(audio_data) / 44100.0

                st.success(f"✓ Recording saved! ({duration:.1f}s)")
                st.audio(audio_bytes, format="audio/wav")

            except Exception as e:
                st.error(f"Audio processing error: {str(e)}")

    except ImportError:
        st.warning("Voice recording feature requires audio-recorder-streamlit package")
    except Exception as e:
        st.error(f"Voice input error: {str(e)}")


def render_lottie_animation(animation_url: str, height: int = 200):
    """
    Render Lottie animation.

    Args:
        animation_url: URL to Lottie animation JSON
        height: Height of animation container
    """
    try:
        from streamlit_lottie import st_lottie
        import requests

        response = requests.get(animation_url, timeout=5)
        if response.status_code == 200:
            st_lottie(response.json(), height=height)

    except ImportError:
        st.info("Animation requires streamlit-lottie")
    except Exception as e:
        # Silently fail for animations - not critical
        pass


def render_chat_message(message: Dict, avatar: str = "💊", show_avatar: bool = True):
    """
    Render a chat message with optional avatar.

    Args:
        message: Message dictionary with 'content' and optional 'role'
        avatar: Avatar emoji/image for this message
        show_avatar: Whether to show the avatar
    """
    role = message.get("role", "assistant")

    with st.chat_message(role, avatar=avatar if show_avatar else None):
        st.markdown(message.get("content", ""))


def render_sample_questions(questions: List[str]):
    """Render sample questions as clickable buttons."""
    st.markdown("### Sample Questions")

    for question in questions:
        if st.button(question, key=f"sample_{hash(question)}"):
            return question

    return None


def render_sources_section(sources: List[Dict]):
    """Render sources/citations section."""
    if not sources:
        return

    st.markdown("### Sources")

    for source in sources:
        with st.expander(f"{source.get('source_type', 'Source')} - {source.get('title', 'Unknown')}"):
            col1, col2 = st.columns(2)

            with col1:
                st.write(f"**Type:** {source.get('source_type', 'N/A')}")
                st.write(f"**Updated:** {source.get('last_updated', 'N/A')}")

            with col2:
                url = source.get('url')
                if url:
                    st.write(f"[Visit Source]({url})")


def render_status_badges(connection_status: Dict):
    """Render status badges for system components."""
    st.sidebar.markdown("### System Status")

    col1, col2, col3 = st.sidebar.columns(3)

    with col1:
        status = "🟢" if connection_status.get("neo4j") else "🔴"
        st.write(f"{status} Neo4j")

    with col2:
        status = "🟢" if connection_status.get("llm") else "🔴"
        st.write(f"{status} LLM")

    with col3:
        status = "🟢" if connection_status.get("voice") else "🔴"
        st.write(f"{status} Voice")
