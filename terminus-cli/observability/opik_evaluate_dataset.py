import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Add src/ to python path
sys.path.append(str(Path(__file__).parent.parent / "src"))

try:
    import opik
    from opik.evaluation import evaluate
    from opik.evaluation.metrics import BaseMetric, score_result
except ImportError as e:
    print(f"Error importing opik: {e}\nEnsure opik is installed correctly.")
    sys.exit(1)

from unittest.mock import patch
from terminus.core.agent import get_or_create_agent
from terminus.core.deps import ToolDeps

# ==============================================================================
# Custom Evaluator / Metric
class ToolsSelectedMetric(BaseMetric):
    """
    Given the Opik string 'expected_tools' from the CSV (e.g. 'find,read_file'),
    and the 'actual_tools' list returned by the AI, checks if the AI called what we needed.
    """
    def __init__(self):
        super().__init__(name="Correct Tool Selection")

    def score(self, expected_tools: str, actual_tools: list[str], **kwargs):
        # CSV stores expected tools as comma-separated: "read_file,grep"
        expected_set = set(expected_tools.split(",")) if expected_tools else set()
        actual_set = set(actual_tools)
        
        # Does the AI output contain at least the tools we expected?
        passed = expected_set.issubset(actual_set)
        
        return score_result.ScoreResult(
            name=self.name,
            value=1.0 if passed else 0.0,
            reason=f"Expected: {expected_set}. AI actually called: {actual_set}"
        )


agent = get_or_create_agent()
custom_metric = ToolsSelectedMetric()

async def _async_agent_task(prompt: str):
    """
    Actually executes the prompt against our LLM asynchronously.
    """
    deps = ToolDeps()
    # Execute the agent natively
    result = await agent.run(prompt, deps=deps)
    
    called_tools = []
    for msg in result.new_messages():
        if hasattr(msg, "parts"):
            for part in msg.parts:
                if getattr(part, "part_kind", None) == "tool-call":
                    called_tools.append(part.tool_name)
                    
    return called_tools, result.data

@opik.track
def agent_task(dataset_item: dict):
    """
    This function processes exactly ONE row from the CSV dataset loaded into Opik.
    Opik automatically passes the row to `dataset_item`.
    Opik's evaluator expects a SYNCHRONOUS function when running natively.
    """
    prompt = dataset_item["prompt"]
    
    try:
        # We manually run the event loop so Opik's ThreadPoolExecutor doesn't crash on coroutines
        called_tools, data = asyncio.run(_async_agent_task(prompt))
        
        # Return exactly the variables the Metric needs to score
        return {
            "expected_tools": dataset_item["expected_tools"], # pass expected forward
            "actual_tools": called_tools,                     # pass actual generated forward
            "model_response": data                            # logged in Opik for UI
        }
    except Exception as e:
        print(f"Error on prompt '{prompt}': {e}")
        return {
             "expected_tools": dataset_item["expected_tools"],
             "actual_tools": [],
             "model_response": str(e)
        }

def evaluate_my_dataset():
    """
    Ties the Opik dataset together with your task and metric.
    """
    DATASET_NAME = "terminus-tool_test" 
    
    print(f"Starting Opik Evaluation on dataset: {DATASET_NAME}...")
    
    client = opik.Opik()
    dataset = client.get_dataset(name=DATASET_NAME)

    # Using Opik's synchronous `evaluate` function, but running an async task
    # Opik handles the event loop and parallelism nicely
    res = evaluate(
        dataset=dataset,
        task=agent_task,
        scoring_metrics=[custom_metric],
        task_threads=2 # How many prompts to run concurrently against Gemini
    )
    print("Evaluation Complete! Check your Opik Dashboard.")

if __name__ == "__main__":
    evaluate_my_dataset()
