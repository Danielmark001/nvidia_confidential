# Project Structure

This document describes the organization of the Medication Advisor AI project.

## Directory Layout

```
nvidia_confidential/
├── config/                     # Configuration files
│   ├── .env.example           # Environment variables template
│   ├── docker-compose.yml     # Docker composition configuration
│   └── nvidia_confidential.code-workspace  # VS Code workspace settings
│
├── data/                       # Data files and datasets
│   ├── questions/             # Test questions for evaluation
│   ├── scenarios/             # Patient scenario data
│   └── src/data/drugbank/     # DrugBank medication database
│
├── docs/                       # Documentation
│   ├── DELIVERY_SUMMARY.txt   # Project delivery summary
│   ├── FILES_CREATED.txt      # List of created files
│   ├── README_SETUP.md        # Setup instructions
│   ├── evaluation_output.txt  # Evaluation results
│   └── evaluation_results.json # Detailed evaluation metrics
│
├── scripts/                    # Utility scripts
│   ├── __init__.py
│   ├── evaluate_system.py     # System evaluation script
│   └── load_data.py           # Data loading script
│
├── src/                        # Main source code
│   ├── __init__.py
│   ├── constants.py           # Application constants
│   │
│   ├── data/                  # Data models and parsers
│   │   ├── __init__.py
│   │   ├── models.py          # Pydantic data models
│   │   └── parsers.py         # Data parsing utilities
│   │
│   ├── etl/                   # Extract, Transform, Load
│   │   ├── __init__.py
│   │   ├── extractors.py      # Data extraction logic
│   │   └── loaders.py         # Data loading to Neo4j
│   │
│   ├── kg/                    # Knowledge Graph operations
│   │   ├── __init__.py
│   │   ├── queries.py         # Cypher query templates
│   │   ├── query_cache.py     # Query result caching
│   │   └── schema.py          # Graph schema management
│   │
│   ├── retrieval/             # RAG and agent components
│   │   ├── __init__.py
│   │   ├── agent.py           # LangChain agent implementation
│   │   ├── query_executor.py  # Query execution logic
│   │   └── tools.py           # Agent tools
│   │
│   ├── scenarios/             # Patient scenario management
│   │   ├── __init__.py
│   │   └── patient_manager.py # Patient scenario handling
│   │
│   ├── services/              # Business logic layer
│   │   ├── __init__.py
│   │   └── medication_service.py  # Medication query service
│   │
│   ├── ui/                    # UI components
│   │   ├── __init__.py
│   │   ├── config_components.py  # Configuration UI
│   │   ├── styles.py           # CSS styling
│   │   └── ui_components.py    # Reusable UI components
│   │
│   ├── utils/                 # Utility modules
│   │   ├── __init__.py
│   │   ├── config.py          # Configuration management
│   │   ├── exceptions.py      # Custom exceptions
│   │   └── logger.py          # Logging utilities
│   │
│   ├── visualization/         # Data visualization
│   │   ├── __init__.py
│   │   └── graph_builder.py   # Graph visualization
│   │
│   └── voice/                 # Voice capabilities
│       ├── __init__.py
│       └── elevenlabs_client.py  # ElevenLabs integration
│
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── test_barebones.py      # Basic functionality tests
│   └── test_nvidia_api.js     # NVIDIA API tests
│
├── .streamlit/                 # Streamlit configuration
│   └── secrets.toml           # Streamlit secrets (gitignored)
│
├── streamlit_app.py           # Main Streamlit application
├── requirements.txt           # Python dependencies
├── README.md                  # Main project documentation
└── .env                       # Environment variables (gitignored)
```

## Module Responsibilities

### Source Code (`src/`)

#### Data Layer (`data/`, `etl/`, `kg/`)
- **data/**: Defines data models and parsing logic for medication records
- **etl/**: Handles extraction and loading of data into Neo4j
- **kg/**: Manages knowledge graph schema, queries, and caching

#### Application Layer (`services/`, `retrieval/`)
- **services/**: Business logic for medication queries and processing
- **retrieval/**: RAG (Retrieval Augmented Generation) and LLM agent implementation

#### Presentation Layer (`ui/`)
- **ui/**: Streamlit UI components, styling, and configuration interfaces

#### Support Modules (`utils/`, `visualization/`, `voice/`, `scenarios/`)
- **utils/**: Cross-cutting concerns (config, logging, exceptions)
- **visualization/**: Graph and data visualization components
- **voice/**: Voice input/output via ElevenLabs
- **scenarios/**: Patient scenario management for demonstrations

### Scripts (`scripts/`)

Utility scripts for development and operations:
- **load_data.py**: Load DrugBank data into Neo4j
- **evaluate_system.py**: Evaluate system performance metrics

### Configuration (`config/`)

Application configuration files:
- **.env.example**: Template for environment variables
- **docker-compose.yml**: Container orchestration
- **workspace settings**: IDE configuration

### Documentation (`docs/`)

Project documentation and reports:
- Setup guides
- Delivery summaries
- Evaluation results

## Key Files

### Application Entry Point
- **streamlit_app.py**: Main Streamlit web application

### Configuration
- **.env**: Environment variables (API keys, database credentials)
- **requirements.txt**: Python package dependencies

### Documentation
- **README.md**: Project overview and main documentation
- **PROJECT_STRUCTURE.md**: This file

## Development Workflow

1. **Setup**: Configure `.env` from `.env.example`
2. **Data Loading**: Run `python scripts/load_data.py`
3. **Development**: Edit source code in `src/`
4. **Testing**: Run tests from `tests/`
5. **Deployment**: Use `config/docker-compose.yml`

## Best Practices

1. **Import Paths**: Always use absolute imports from project root
   ```python
   from src.services.medication_service import MedicationQueryService
   ```

2. **Configuration**: Store all secrets in `.env`, never commit them
3. **Tests**: Add tests to `tests/` directory
4. **Scripts**: Put utility scripts in `scripts/` directory
5. **Documentation**: Update `docs/` when adding features

## Notes

- All `__pycache__` and `venv/` directories are gitignored
- Data files are stored in `data/` but large files should use `.gitignore`
- The project follows a clean architecture with separated layers
