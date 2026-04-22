# Terminus CLI

Terminus is a terminal-native AI automation assistant that executes real work through a tool-first architecture.

It is built for engineering workflows where natural-language requests should result in transparent, controlled terminal actions.

## Table of Contents

- [Why Terminus](#why-terminus)
- [Capabilities](#capabilities)
- [Requirements](#requirements)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Command Reference](#command-reference)
- [Safety and Execution Model](#safety-and-execution-model)
- [Evaluation and Observability](#evaluation-and-observability)
- [Development Workflow](#development-workflow)
- [Project Layout](#project-layout)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## Why Terminus

- Terminal-first workflow with no IDE dependency.
- Single-agent orchestration with specialized tool execution.
- Session-aware runtime context (history, working directory, preferences).
- Confirmation gates for risky actions.
- Extensible architecture for adding tools and integrations.

![Terminus architecture](docs/terminus-arch.png)

Architecture documentation:

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## Capabilities

- Natural-language execution for file, project, and system workflows.
- Tool-driven operations for search, edits, analysis, and shell execution.
- Development workflows for Git, project scaffolding, and code insights.
- Gmail and Calendar integrations with explicit safety boundaries.
- Model management with cloud and local fallback support.
- Session persistence and command/context tracking across runs.

## Requirements

- Python 3.10+
- Gemini API key for cloud model usage
- Optional: Ollama for local/offline model usage
- Optional: Google OAuth credentials for Gmail/Calendar integrations

## Installation

### Option A: pipx (recommended)

```bash
pip install pipx
pipx install terminus-cli
```

### Option B: pip

```bash
pip install terminus-cli
```

### Option C: local development setup

```bash
git clone <repository-url>
cd terminus-cli
python -m venv env
```

Windows:

```bash
env\Scripts\activate
```

macOS/Linux:

```bash
source env/bin/activate
```

Install runtime and developer dependencies:

```bash
pip install -e .
pip install pytest pytest-asyncio python-dotenv opik
```

## Quick Start

Launch Terminus:

```bash
terminus
```

On first run, setup creates and validates config, then collects required credentials.

Example prompts:

```text
analyze this project structure and suggest improvements
find all TODO comments and summarize by file
show files larger than 100MB
schedule a 30-minute meeting tomorrow at 2pm
```

## Configuration

Default config path:

- `~/.config/terminus.json`

Minimum config example:

```json
{
  "default_model": "google-gla:gemini-2.5-flash",
  "env": {
    "GEMINI_API_KEY": "your-api-key"
  }
}
```

Optional integration keys:

- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`

Runtime updates are available via command interface:

- `/config`
- `/config key <new_api_key>`
- `/config model <model_name>`

## Command Reference

### Basic

- `/help`
- `/status`
- `/version`
- `/clear`
- `/yolo` (disables confirmations for the current session)

### Context and Memory

- `/dump`
- `/history`
- `/tag create <name> [notes]`
- `/tag remove <name>`
- `/switch #<tag>`

### Models and Runtime

- `/models`
- `/switch <model_name>`
- `/offline`
- `/config`

### Session Management

- `/sessions [--clear]`
- `/save [name]`
- `/load <name>`
- `/cleanup`

## Safety and Execution Model

- Non-destructive operations run directly.
- Risky or destructive operations require confirmation by default.
- Per-tool "always allow" can be set within a session.
- `/yolo` bypasses confirmation prompts and should be used with caution.

## Evaluation and Observability

Generate and run routing evaluations:

```bash
python evals/generate_evals.py
pytest evals/test_evals.py
```

Run Opik-based evaluation pipeline:

```bash
python observability/opik_evaluate_dataset.py
```

Configure environment values before observability runs:

- [observability/.env.example](observability/.env.example)

## Development Workflow

Run tests:

```bash
pytest
```

Run targeted evaluation tests:

```bash
pytest evals/test_evals.py
```

## Project Layout

```text
src/terminus/
  core/
  tools/
  infrastructure/
  ui/
  utils/
docs/
evals/
observability/
```

## Troubleshooting

- If model calls fail, verify API key and model selection with `/models` and `/status`.
- If local model usage is expected, ensure Ollama is running before `/offline`.
- If integrations fail, validate OAuth credentials in config and environment.
- If behavior seems stale, use `/clear` to reset conversation state.

## License

MIT
