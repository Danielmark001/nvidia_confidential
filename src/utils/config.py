import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False

load_dotenv()

def get_config_value(key: str, default: str = "") -> str:
    if HAS_STREAMLIT:
        try:
            return st.secrets.get(key, os.getenv(key, default))
        except (FileNotFoundError, AttributeError):
            return os.getenv(key, default)
    return os.getenv(key, default)

class Config:
    """Configuration management for the medication advisor application."""

    # NVIDIA NIM Configuration
    NVIDIA_API_KEY: str = get_config_value("NVIDIA_API_KEY", "")
    LLM_MODEL: str = get_config_value("LLM_MODEL", "meta/llama-3.1-70b-instruct")
    LLM_TEMPERATURE: float = float(get_config_value("LLM_TEMPERATURE", "0.0"))
    LLM_MAX_TOKENS: int = int(get_config_value("LLM_MAX_TOKENS", "1024"))
    LLM_BASE_URL: Optional[str] = get_config_value("LLM_BASE_URL") or None

    # Neo4j Configuration
    NEO4J_URI: str = get_config_value("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USERNAME: str = get_config_value("NEO4J_USERNAME", "neo4j")
    NEO4J_PASSWORD: str = get_config_value("NEO4J_PASSWORD", "")

    # Data Paths
    PROJECT_ROOT: Path = Path(__file__).parent.parent.parent
    DATA_DIR: Path = PROJECT_ROOT / get_config_value("DATA_DIR", "data")
    I2B2_DATA_PATH: Path = PROJECT_ROOT / get_config_value("I2B2_DATA_PATH", "data/i2b2_2014")
    DRUGBANK_DATA_PATH: Path = PROJECT_ROOT / get_config_value("DRUGBANK_DATA_PATH", "data/drugbank")

    # Logging
    LOG_LEVEL: str = get_config_value("LOG_LEVEL", "INFO")

    # ElevenLabs (for future use)
    ELEVENLABS_API_KEY: str = get_config_value("ELEVENLABS_API_KEY", "")
    ELEVENLABS_VOICE_ID: str = get_config_value("ELEVENLABS_VOICE_ID", "")

    @classmethod
    def validate(cls) -> bool:
        """Validate that required configuration values are set."""
        errors = []

        if not cls.NVIDIA_API_KEY:
            errors.append("NVIDIA_API_KEY is not set")

        if not cls.NEO4J_PASSWORD:
            errors.append("NEO4J_PASSWORD is not set")

        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")

        return True

    @classmethod
    def ensure_data_dirs(cls):
        """Create data directories if they don't exist."""
        cls.DATA_DIR.mkdir(exist_ok=True, parents=True)
        cls.I2B2_DATA_PATH.mkdir(exist_ok=True, parents=True)
        cls.DRUGBANK_DATA_PATH.mkdir(exist_ok=True, parents=True)


config = Config()
