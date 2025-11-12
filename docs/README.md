# Documentation

This directory contains project documentation and reports.

## Available Documentation

### Setup and Configuration
- See [../README.md](../README.md) for project overview
- See [../config/.env.example](../config/.env.example) for environment setup

### Development
- See [../CONTRIBUTING.md](../CONTRIBUTING.md) for development guidelines
- See [../PROJECT_STRUCTURE.md](../PROJECT_STRUCTURE.md) for project organization

## Directory Purpose

Place additional documentation here:
- API documentation
- Architecture diagrams
- User guides
- Technical specifications
- Evaluation reports
- Performance benchmarks

## Generating Documentation

### From Code Docstrings
```bash
# Install sphinx
pip install sphinx sphinx-rtd-theme

# Generate docs
cd docs
sphinx-quickstart
sphinx-apidoc -o . ../src
make html
```

### From Markdown
Use tools like MkDocs:
```bash
pip install mkdocs mkdocs-material
mkdocs serve
```
