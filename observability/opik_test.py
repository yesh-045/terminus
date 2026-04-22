import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file (if present)
load_dotenv()

# Fix python path so we can import from src
sys.path.append(str(Path(__file__).parent.parent / "src"))



try:
    import opik
    from opik import track
    from opik import opik_context
except ImportError:
    print("Opik is not installed. Run: pip install opik")
    sys.exit(1)

from terminus.core.agent import get_or_create_agent
from terminus.core.deps import ToolDeps
from terminus.core.session import session

# Initialize agent
agent = get_or_create_agent()

@track
async def execute_terminus_request(prompt: str):
    """
    This function is wrapped with Opik's @track decorator. 
    It will capture the input prompt, outputs, exceptions, and execution time 
    and push it seamlessly to your Opik dashboard.
    """
    print(f"Executing: '{prompt}'")
    deps = ToolDeps()
    
    # You can attach custom metadata/tags to the Opik Trace
    opik_context.update_current_trace(
        tags=["cli-agent", "development"],
        metadata={
            "agent_model": session.current_model,
            "session_dir": str(session.working_directory),
            "python_version": sys.version.split(" ")[0]
        }
    )

    try:
        # Run the agent action
        result = await agent.run(prompt, deps=deps)
        
        # Extract the tools the LLM decided to use
        tool_calls = []
        for msg in result.new_messages():
            if hasattr(msg, "parts"):
                for part in msg.parts:
                    if getattr(part, "part_kind", None) == "tool-call":
                        tool_calls.append(part.tool_name)
                        
        print(f"\n[AI Generated Outputs] -> {result.data}\n[Tools Used] -> {tool_calls}")
        
        # Return structured data, Opik will log this JSON automatically
        return {
            "response": result.data,
            "tools_called": tool_calls,
            "latency_metadata": "tracked automatically by @track"
        }
        
    except Exception as e:
        # Opik will also catch and trace exceptions automatically!
        print(f"Evaluation Failed: {e}")
        raise e

async def main():
    print("Starting Terminus Observability Demo with Opik...")
    print("Ensure you have set the OPIK_API_KEY env variable to view traces online.\n")
    
    # Test Prompts
    prompts = [
        "What files are in my current directory?",
        "Can you read the contents of the Architecture.md file?"
    ]
    
    for prompt in prompts:
        print(f"\n--- Running Prompt ---")
        await execute_terminus_request(prompt)

if __name__ == "__main__":
    asyncio.run(main())
