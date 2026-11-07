# template_orchestrator_agent.py
"""
Orchestrator Agent — Ready-to-use template
Dependencies: pip install openai-agents==0.24.0 langgraph langchain-openai python-dotenv
"""
import asyncio
import json
import logging
import time
from datetime import datetime
from typing import TypedDict, Optional, Annotated
from dotenv import load_dotenv
from agents import Agent, Runner, function_tool, handoff, WebSearchTool

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────
# SPECIALIZED AGENTS
# ─────────────────────────────────────────
collection_agent = Agent(
    name="CollectionAgent",
    model="gpt-5.4-mini",
    instructions="""You collect raw information on a given topic.
    You use WebSearch to find recent and reliable data.
    You return only facts, without analysis or opinion.
    Output format: list of facts with a source for each fact.""",
    tools=[WebSearchTool()],
)

analysis_agent = Agent(
    name="AnalysisAgent",
    model="gpt-5.4-mini",
    instructions="""You receive raw data and analyze it.
    You identify:
    - The main trends (2-3 max)
    - Contradictory data
    - What is certain vs uncertain
    - Practical implications
    You do not repeat the raw data, you interpret it.""",
)

synthesis_agent = Agent(
    name="SynthesisAgent",
    model="gpt-5.4-mini",
    instructions="""You receive an analysis and transform it into an actionable deliverable.
    Format according to the requested type:
    - report: title -> executive summary -> 3 recommendations -> risks
    - article: hook -> 3 parts -> conclusion CTA
    - brief: 5 bullets maximum, directly actionable
    Be precise, get to the point.""",
)

# ─────────────────────────────────────────
# ORCHESTRATOR TOOLS
# ─────────────────────────────────────────
# WARNING: this module-level cache is fine for a single-run demo.
# In a server (FastAPI, scheduled batch, anything multi-tenant), two concurrent
# requests would clobber each other's state. For real usage, pass results via
# the run context (RunContextWrapper) or accumulate them in a dict scoped to
# the request, not a module global.
_results_cache: dict = {}

@function_tool
async def delegate_collection(subject: str) -> str:
    """
    Delegate information collection to the specialized agent.
    
    Args:
        subject: The topic to collect information about
    """
    logger.info(f"[Collection] Starting for: {subject}")
    result = await Runner.run(collection_agent, input=f"Collect information on: {subject}", max_turns=5)
    _results_cache["collection"] = result.final_output
    logger.info(f"[Collection] Complete ({len(result.final_output)} characters)")
    return result.final_output

@function_tool
async def delegate_analysis(data: str, context: str = "") -> str:
    """
    Delegate analysis to the specialized agent.
    
    Args:
        data: The raw data to analyze
        context: Additional context for the analysis
    """
    logger.info("[Analysis] Starting")
    
    analysis_input = f"Analyze this data:{context}\n\nData:\n{data}"
    result = await Runner.run(analysis_agent, input=analysis_input, max_turns=3)
    _results_cache["analysis"] = result.final_output
    logger.info("[Analysis] Complete")
    return result.final_output

@function_tool
async def delegate_synthesis(
    analysis: str,
    output_format: str = "rapport",
    audience: str = "développeurs"
) -> str:
    """
    Delegate final synthesis to the specialized agent.
    
    Args:
        analysis: The analysis to synthesize
        output_format: Desired format (rapport, article, brief)
        audience: The target audience
    """
    logger.info(f"[Synthesis] Format: {output_format}")
    
    synthesis_input = f"""Create a {output_format} for {audience} based on this analysis:

{analysis}

Desired format: {output_format}"""
    
    result = await Runner.run(synthesis_agent, input=synthesis_input, max_turns=3)
    _results_cache["synthesis"] = result.final_output
    logger.info("[Synthesis] Complete")
    return result.final_output

@function_tool
def save_workflow(name: str) -> str:
    """
    Save all results from the current workflow.
    
    Args:
        name: Name identifying this workflow
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = f"workflow_{name}_{timestamp}.json"
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump({
            "name": name,
            "timestamp": datetime.now().isoformat(),
            "results": _results_cache
        }, f, ensure_ascii=False, indent=2)
    
    return f"Workflow saved: {filepath}"

# ─────────────────────────────────────────
# MAIN ORCHESTRATOR
# ─────────────────────────────────────────
orchestrator = Agent(
    name="Orchestrator",
    model="gpt-5.4-mini",
    instructions="""You coordinate an intelligence production pipeline.

You receive a request and orchestrate:
1. delegate_collection() -> gather raw information
2. delegate_analysis() -> analyze the collected data
3. delegate_synthesis() -> create the final deliverable
4. save_workflow() -> archive everything

You adapt the output_format based on the request:
- "market analysis" -> report format
- "blog article" -> article format
- "quick summary" -> brief format

You report errors clearly and suggest alternatives.
You do not do the work of the specialized agents — you coordinate.""",
    tools=[
        delegate_collection,
        delegate_analysis,
        delegate_synthesis,
        save_workflow,
    ],
)

# ─────────────────────────────────────────
# MAIN INTERFACE
# ─────────────────────────────────────────
async def orchestrate(request: str) -> str:
    """Launch the complete pipeline for a request."""
    logger.info(f"=== New workflow: {request[:50]} ===")
    
    start = time.time()
    
    result = await Runner.run(
        orchestrator,
        input=request,
        max_turns=12
    )
    
    duration = time.time() - start
    logger.info(f"=== Workflow complete in {duration:.1f}s ===")
    
    return result.final_output

async def main():
    """Template demo."""
    requests = [
        "Fais une analyse de marché sur les frameworks d'agents IA open source en 2026",
        "Crée un article de blog sur les bonnes pratiques de déploiement d'agents IA",
    ]
    
    for request in requests:
        print(f"\n{'='*60}")
        print(f"Request: {request}")
        print('='*60)
        
        result = await orchestrate(request)
        print(f"\n{result}")

if __name__ == "__main__":
    asyncio.run(main())
