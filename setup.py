"""Setup configuration for Medication Advisor AI."""

from setuptools import setup, find_packages
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="medication-advisor-ai",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="AI-powered medication advisory system using NVIDIA NIM, Neo4j, and ElevenLabs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/medication-advisor-ai",
    packages=find_packages(exclude=["tests*", "scripts*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Healthcare Industry",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "streamlit>=1.28.0",
        "neo4j>=5.12.0",
        "openai>=1.3.0",
        "langchain>=0.1.0",
        "langchain-nvidia-ai-endpoints>=0.0.11",
        "python-dotenv>=1.0.0",
        "elevenlabs>=0.2.0",
        "audio-recorder-streamlit>=0.0.8",
        "soundfile>=0.12.0",
        "numpy>=1.24.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.7.0",
            "flake8>=6.1.0",
            "mypy>=1.5.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "medication-advisor=streamlit_app:main",
            "load-data=scripts.load_data:main",
            "evaluate-system=scripts.evaluate_system:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.json", "*.yaml", "*.yml"],
    },
)
