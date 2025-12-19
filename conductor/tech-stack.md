# Technology Stack: Obsidian CLI Ops

## Core Languages & Frameworks
- **Python 3.9+**: Primary language for backend logic, graph analysis, and TUI.
- **Zsh**: Used for CLI entry points, shell integration, and high-performance system tasks.
- **Node.js/JavaScript**: Used for specific integration tests and legacy shell script testing.

## Frontend & UI (Terminal)
- **Textual**: Modern TUI framework used for building interactive, ADHD-friendly terminal applications.
- **Rich**: Foundation for Textual, used for beautiful console formatting, progress bars, and dashboards.
- **Click / Typer**: Frameworks for building the command-line interface and handling arguments.

## Data & Knowledge Graph
- **SQLite**: Local, zero-config database for storing vault metadata, link relationships, and scan history.
- **NetworkX**: Robust Python library for complex knowledge graph analysis (PageRank, centrality, etc.).

## AI & Machine Learning
- **Multi-Provider AI Strategy**:
  - **Gemini API**: For high-performance cloud-based analysis.
  - **Ollama**: For 100% local, private LLM execution.
  - **HuggingFace (sentence-transformers)**: For local embedding generation and semantic similarity analysis.

## Infrastructure & Tooling
- **Testing**:
  - **Pytest**: Primary testing framework for Python code.
  - **Jest**: Used for JavaScript-based integration and shell testing.
- **Code Quality**:
  - **Black / Flake8 / Mypy**: Python linting, formatting, and type checking.
  - **ESLint / Prettier**: JavaScript linting and formatting.
- **Documentation**:
  - **MkDocs (Material)**: For generating the project's static documentation site.
