# template_research_agent.py
"""
Research Agent — Ready-to-use template
Dependencies: pip install openai-agents==0.24.0 python-dotenv httpx
"""
import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv
from agents import Agent, Runner, WebSearchTool, function_tool
import httpx
import logging

logger = logging.getLogger(__name__)
load_dotenv()

# ─────────────────────────────────────────
# CONFIGURATION (customize as needed)
# ─────────────────────────────────────────
AGENT_NAME = "ResearchAgent"
LANGUAGE = "français"
DOMAIN = "technologie et développement Python"
MAX_RESULTS_PER_SEARCH = 5
TIMEOUT_SECONDS = 30

# ─────────────────────────────────────────
# TOOLS
# ─────────────────────────────────────────
@function_tool
async def search_hacker_news(query: str) -> list[dict]:
    """
    Search Hacker News via the official API (free, no key required).

    Args:
        query: The keywords to search for
    """
    # Use params= (not f-string) so httpx URL-encodes the query for us.
    # Otherwise a query like "AI&safety" would break the URL.
    params = {
        "query": query,
        "hitsPerPage": MAX_RESULTS_PER_SEARCH,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(
                "https://hn.algolia.com/api/v1/search",
                params=params,
            )
            resp.raise_for_status()
            data = resp.json()

            return [
                {
                    "title":    hit.get("title", ""),
                    "url":      hit.get("url", ""),
                    "points":   hit.get("points", 0),
                    "comments": hit.get("num_comments", 0),
                    "author":   hit.get("author", ""),
                    "date":     hit.get("created_at", ""),
                }
                for hit in data.get("hits", [])
                if hit.get("title")
            ]
        except httpx.HTTPError as e:
            # Don't leak internal exception details to the LLM/user.
            # Log the real error server-side; surface a stable message.
            logger.warning("HN search failed: %s", e)
            return [{"error": "Search temporarily unavailable. Try again."}]

@function_tool
def format_report(
    title: str,
    key_points: list[str],
    sources: list[str],
    conclusion: str
) -> str:
    """
    Format a structured report.
    
    Args:
        title: Report title
        key_points: List of main points (3-5 items)
        sources: URLs of sources used
        conclusion: Actionable conclusion in 1-2 sentences
    """
    date = datetime.now().strftime("%d/%m/%Y")
    report = f"# {title}\n*{date}*\n\n## Points clés\n\n"
    
    for i, point in enumerate(key_points, 1):
        report += f"{i}. {point}\n"
    
    report += f"\n## Conclusion\n\n{conclusion}\n\n"
    
    if sources:
        report += "## Sources\n\n"
        for source in sources:
            report += f"- {source}\n"
    
    return report

# ─────────────────────────────────────────
# AGENT
# ─────────────────────────────────────────
research_agent = Agent(
    name=AGENT_NAME,
    model="gpt-5.4-mini",
    instructions=f"""You are a research agent specializing in {DOMAIN}.
    
    You always respond in {LANGUAGE}.
    
    For each research request:
    1. Identify the relevant keywords
    2. Launch targeted searches (WebSearch + Hacker News if relevant)
    3. Synthesize the information found
    4. Format a structured report with format_report()
    
    Rules:
    - Always cite your sources
    - Indicate when information is more than 6 months old
    - Only present verifiable facts, flag opinions as such
    - If you cannot find reliable information, say so clearly""",
    tools=[
        WebSearchTool(),
        search_hacker_news,
        format_report,
    ],
)

# ─────────────────────────────────────────
# MAIN INTERFACE
# ─────────────────────────────────────────
async def search(question: str) -> str:
    """Main entry point."""
    try:
        result = await asyncio.wait_for(
            Runner.run(research_agent, input=question, max_turns=8),
            timeout=TIMEOUT_SECONDS
        )
        return result.final_output
    except asyncio.TimeoutError:
        return f"[TIMEOUT] Search exceeded ({TIMEOUT_SECONDS}s). Please rephrase the question."
    except Exception as e:
        return f"[ERROR] {str(e)}"

async def main():
    """Template demo."""
    questions = [
        "What are the latest features of the OpenAI Agents SDK?",
        "What are the most popular Python frameworks in 2026?",
    ]
    
    for question in questions:
        print(f"\n{'='*60}")
        print(f"Question: {question}")
        print('='*60)
        response = await search(question)
        print(response)

if __name__ == "__main__":
    asyncio.run(main())
