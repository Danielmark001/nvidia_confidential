"""Reusable UI components for the Streamlit app."""

import streamlit as st
from typing import Dict, List, Tuple, Optional
import os


def render_avatar_selector():
    """Render avatar selection in sidebar."""
    st.sidebar.markdown("### Avatar Settings")

    avatar_options = {
        "Doctor": "🏥",
        "Medical Bot": "🤖",
        "Assistant": "💊"
    }

    selected_avatar = st.sidebar.selectbox(
        "AI Advisor Avatar",
        options=list(avatar_options.keys()),
        index=1
    )

    return avatar_options.get(selected_avatar, "🤖")


def render_demo_mode_toggle():
    """Render demo mode toggle in sidebar."""
    st.sidebar.markdown("### Demo Mode")

    demo_mode = st.sidebar.toggle("Enable Demo Mode", value=False)

    return demo_mode


def render_patient_selector(patient_scenarios: List[Dict]) -> Optional[Dict]:
    """Render patient scenario selector."""
    if not patient_scenarios:
        st.warning("No patient scenarios available")
        return None

    st.sidebar.markdown("### Patient Scenario")

    patient_names = [f"{s['name']} ({s['age']}y)" for s in patient_scenarios]

    selected_idx = st.sidebar.selectbox(
        "Select Patient",
        range(len(patient_scenarios)),
        format_func=lambda i: patient_names[i]
    )

    return patient_scenarios[selected_idx]


def render_patient_card(patient: Dict):
    """Render patient information card."""
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Patient Name", patient.get("name", "Unknown"))

    with col2:
        st.metric("Age", patient.get("age", "N/A"))

    with col3:
        st.metric("Situation", "Discharged" if patient.get("discharge_date") else "Admitted")

    st.info(f"**Clinical Context:** {patient.get('context', 'N/A')}")


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
    """Render voice input component using file upload."""
    st.info("📁 Upload an audio file or use the file uploader below to ask by voice")

    audio_file = st.file_uploader(
        "Choose an audio file",
        type=["wav", "mp3", "ogg", "m4a", "webm"],
        key="voice_file_uploader",
        label_visibility="collapsed"
    )

    if audio_file:
        st.audio(audio_file, format="audio/wav")
        return audio_file

    return None


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
