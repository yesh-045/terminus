# Terminus Observability with Opik

This directory contains integration scripts for tracking and observing the LLM outputs and logic inside Terminus using **Opik (by Comet)**. 

### Why Opik?
Opik purely for tracing, and measuring "perceived latency" metrics—understanding *why* the `Agent` takes certain turns, exactly what context the Prompt received under the hood, and tracking token usage over time.

### Quick Setup

1. **Install Dependencies**:
   ```bash
   pip install opik python-dotenv
   ```
2. **Setup your `.env` File**:
   Copy `.env.example` to a new `.env` file in the `observability/` folder:
   ```bash
   cp .env.example .env
   ```
   Add your Opik API key and Workspace ID (Create a free account on Comet/Opik if you haven't).

3. **Run the Demo**:
   ```bash
   python opik_demo.py
   ```

### What You'll See in the Dashboard
By simply using the `@track` decorator on your execution chain:
- **Trace DAG**: The exact inputs going to the model, and the outputs coming from it in a visual node graph.
- **Latency Over Time**: A graph showing how long `Agent.run` takes across multiple different Prompts.
- **Metadata**: The Python version, Model name, and custom Context details you provided logged next to the execution state.
- **Token Efficiency**: A visualization of the token size of `session.messages` as it grows inside a loop.