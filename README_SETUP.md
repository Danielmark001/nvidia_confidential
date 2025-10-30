# Medication Advisor Setup Guide

This guide will walk you through setting up the Medication Advisor AI system with NVIDIA NIM, Neo4j, and LangChain.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Neo4j Setup](#neo4j-setup)
4. [Configuration](#configuration)
5. [Data Acquisition](#data-acquisition)
6. [Running the System](#running-the-system)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.8+** (Python 3.10+ recommended)
- **Neo4j Desktop** or **Neo4j Aura** account
- **NVIDIA API Key** (free tier available)
- **Git** (for cloning the repository)

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd nvidia-nim-pipeline
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## Neo4j Setup

You have two options for Neo4j: Desktop (local) or Aura (cloud).

### Option A: Neo4j Desktop (Recommended for Development)

1. **Download Neo4j Desktop**
   - Visit: https://neo4j.com/download/
   - Download and install Neo4j Desktop

2. **Create a New Project**
   - Open Neo4j Desktop
   - Click "New" → "Create Project"
   - Name it "Medication Advisor"

3. **Create a Database**
   - Click "Add" → "Local DBMS"
   - Name: `medication-advisor`
   - Password: Choose a strong password (you'll need this later)
   - Version: 5.x (latest stable)
   - Click "Create"

4. **Start the Database**
   - Click "Start" on your database
   - Wait for it to show "Active"
   - Note the connection details:
     - URI: `bolt://localhost:7687`
     - Username: `neo4j`
     - Password: (your chosen password)

### Option B: Neo4j Aura (Cloud)

1. **Create Aura Account**
   - Visit: https://neo4j.com/cloud/aura/
   - Sign up for free tier

2. **Create Instance**
   - Click "Create instance"
   - Select "Free" tier
   - Name: `medication-advisor`
   - Click "Create"

3. **Download Credentials**
   - Download the credentials file
   - Note the connection details:
     - URI: `neo4j+s://xxxxx.databases.neo4j.io`
     - Username: `neo4j`
     - Password: (generated password)

## Configuration

### 1. Create Environment File

Copy the example environment file:

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

### 2. Get NVIDIA API Key

1. Visit: https://build.nvidia.com/
2. Sign in or create account
3. Click on your profile → "Get API Key"
4. Copy the API key (starts with `nvapi-`)

### 3. Edit .env File

Open `.env` in a text editor and fill in your credentials:

```env
# NVIDIA NIM API Configuration
NVIDIA_API_KEY=nvapi-your-actual-api-key-here

# Neo4j Database Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-neo4j-password-here

# For Neo4j Aura, use:
# NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
```

### 4. Verify Configuration

Test your configuration:

```bash
python -c "from src.utils.config import config; config.validate(); print('Configuration OK!')"
```

## Data Acquisition

You have two options: use sample data for testing, or obtain real datasets.

### Option A: Sample Data (Quick Start)

Generate sample discharge notes and medication data:

```bash
python -m src.data.downloaders
```

When prompted, type `y` to create sample data.

### Option B: Real Datasets

#### i2b2 2014 Discharge Summaries

1. Visit: https://portal.dbmi.hms.harvard.edu/
2. Create account and sign in
3. Request access to "2014 De-identification Challenge"
4. Sign Data Use Agreement
5. Wait for approval (24-48 hours)
6. Download and extract to `data/i2b2_2014/`

#### DrugBank Open Data

1. Visit: https://go.drugbank.com/
2. Create free account
3. Navigate to Downloads
4. Download "DrugBank Open Data" (TSV format)
5. Extract to `data/drugbank/`

For detailed instructions, run:

```bash
python -m src.data.downloaders
```

## Running the System

### Initial Setup (First Time Only)

Run the interactive demo to set up everything:

```bash
python demo.py
```

Then follow the menu:
1. Select option 1: "Setup Knowledge Graph Schema"
2. Select option 2: "Load Sample Data"

Or use the quick setup command:

```bash
python demo.py --setup
```

### Interactive Chat

Start a chat session with the medication advisor:

```bash
python demo.py --chat
```

Or through the menu:

```bash
python demo.py
# Select option 6: "Start Interactive Chat"
```

### Single Question Mode

Ask a single question:

```bash
python demo.py --question "How should I take Metformin?"
```

### View Database Statistics

Check what's in your knowledge graph:

```bash
python demo.py --stats
```

## Usage Examples

### Example Questions

Try asking the medication advisor:

```
How should I take Metformin?
What is Lisinopril used for?
Are there any interactions between Aspirin and Warfarin?
What medications should I avoid with my diabetes?
What are my discharge instructions?
Tell me about Atorvastatin
```

### Running ETL Pipeline

Load your own discharge notes:

```bash
python -m src.etl.loaders
```

Or use the menu option 5 in `demo.py`.

### Testing Individual Components

Test the Neo4j schema:

```bash
python -m src.kg.schema
```

Test the query builders:

```bash
python -m src.kg.queries
```

Test the parsers:

```bash
python -m src.data.parsers
```

## Project Structure

```
nvidia-nim-pipeline/
├── src/
│   ├── data/           # Data acquisition and parsing
│   ├── etl/            # Extract-Transform-Load pipeline
│   ├── kg/             # Knowledge graph (Neo4j)
│   ├── retrieval/      # LLM agent and tools
│   └── utils/          # Configuration and utilities
├── data/               # Data storage (gitignored)
├── notebooks/          # Jupyter notebooks
├── demo.py             # Main demo script
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template
└── README_SETUP.md     # This file
```

## Troubleshooting

### "Cannot connect to Neo4j"

**Solution:**
1. Verify Neo4j is running (Desktop: check status, Aura: check instance)
2. Check connection details in `.env` file
3. Test connection:
   ```bash
   python -m src.kg.schema
   ```

### "NVIDIA_API_KEY is not set"

**Solution:**
1. Ensure you copied `.env.example` to `.env`
2. Add your API key to `.env` file
3. Restart your terminal/IDE to reload environment

### "No module named 'src'"

**Solution:**
1. Make sure you're in the project root directory
2. Verify virtual environment is activated
3. Reinstall dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### "No medications found in knowledge graph"

**Solution:**
1. Load data first:
   ```bash
   python demo.py --load-sample
   ```
2. Verify data was loaded:
   ```bash
   python demo.py --stats
   ```

### Import Errors

**Solution:**
1. Ensure all `__init__.py` files exist
2. Reinstall in development mode:
   ```bash
   pip install -e .
   ```

### Neo4j Authentication Failed

**Solution:**
1. Double-check password in `.env` matches Neo4j password
2. For Neo4j Desktop: check database settings
3. For Aura: regenerate credentials if needed

## Next Steps

After setup, you can:

1. **Explore the Knowledge Graph**
   - Open Neo4j Browser (http://localhost:7474 for Desktop)
   - Run Cypher queries to explore the data

2. **Add More Data**
   - Obtain i2b2 and DrugBank datasets
   - Run ETL pipeline with real data

3. **Customize the Agent**
   - Modify prompts in `src/retrieval/agent.py`
   - Add new tools in `src/retrieval/tools.py`

4. **Evaluate Performance**
   - Create test questions
   - Measure F1 scores and citation precision
   - See evaluation plan in main README.md

5. **Build Streamlit UI**
   - Add Streamlit and ElevenLabs integration
   - Implement voice I/O

## Support

For issues and questions:
- Check the main [README.md](README.md) for project details
- Review the [evaluation plan](README.md#evaluation-plan)
- Check Neo4j documentation: https://neo4j.com/docs/
- Check LangChain documentation: https://python.langchain.com/
- NVIDIA NIM documentation: https://developer.nvidia.com/nim

## System Requirements

**Minimum:**
- 8GB RAM
- 10GB disk space
- Internet connection

**Recommended:**
- 16GB+ RAM
- SSD storage
- Stable internet for API calls

## Performance Tips

1. **Batch Loading**: Load large datasets in batches
2. **Indexes**: Ensure fulltext indexes are created
3. **Connection Pooling**: Reuse Neo4j connections
4. **API Rate Limits**: NVIDIA free tier has rate limits
5. **Local NIM**: For production, consider hosting NIM locally

## Security Notes

- Never commit `.env` file to version control
- Keep API keys secure
- Use strong Neo4j passwords
- For production, use Neo4j authentication and encryption

## License

See main README.md for license information.
