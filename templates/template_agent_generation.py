# template_agent_generation.py
"""
Generation Agent — Ready-to-use template
Dependencies: pip install openai-agents==0.24.0 python-dotenv
"""
import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import Literal
from dotenv import load_dotenv
from agents import Agent, Runner, function_tool
from pydantic import BaseModel

load_dotenv()

# ─────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────
AGENT_NAME = "GenerationAgent"
LANGUAGE = "français"
STYLE = "professionnel, direct, sans jargon inutile"
AUDIENCE = "développeurs Python juniors à seniors"
OUTPUT_DIR = Path("./outputs")

# ─────────────────────────────────────────
# DATA MODELS
# ─────────────────────────────────────────
class ContentBrief(BaseModel):
    type: Literal["article", "email", "documentation", "rapport", "readme"]
    subject: str
    audience: str = AUDIENCE
    length: Literal["court", "moyen", "long"] = "moyen"
    required_points: list[str] = []
    tone: Literal["formel", "neutre", "conversationnel"] = "neutre"

# ─────────────────────────────────────────
# TOOLS
# ─────────────────────────────────────────
import re

def _safe_filename(name: str) -> str:
    """Strip anything that's not a-zA-Z0-9_-, cap at 80 chars.
    Prevents path traversal (../../etc/passwd) and weird chars from the LLM."""
    cleaned = re.sub(r"[^a-zA-Z0-9_-]", "_", name)
    return cleaned[:80] or "content"


@function_tool
def save_content(
    filename: str,
    content: str,
    format: Literal["md", "txt", "html"] = "md",
) -> str:
    """
    Save the generated content to a file under OUTPUT_DIR.

    Args:
        filename: File name without extension (will be sanitized)
        content: The content to save
        format: Output format (md, txt, html)
    """
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_root = OUTPUT_DIR.resolve()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = _safe_filename(filename)
    filepath = (output_root / f"{safe_name}_{timestamp}.{format}").resolve()

    # Defense in depth: ensure the resolved path stays under OUTPUT_DIR.
    if output_root not in filepath.parents and filepath.parent != output_root:
        return "Error: filename produces a path outside the output directory"

    filepath.write_text(content, encoding="utf-8")
    return f"Content saved: {filepath.name} ({len(content)} characters)"

@function_tool
def evaluate_content(content: str) -> dict:
    """
    Evaluate the quality of content against objective criteria.
    
    Args:
        content: The content to evaluate
    """
    words = content.split()
    sentences = content.split('.')
    
    # Basic criteria
    score = 100
    issues = []
    
    if len(words) < 50:
        score -= 20
        issues.append("Content too short (< 50 words)")
    
    if len(set(words)) / max(len(words), 1) < 0.5:
        score -= 15
        issues.append("Vocabulary too repetitive")
    
    # Check for structure
    if "##" not in content and "**" not in content:
        score -= 10
        issues.append("No visible structure (headings or emphasis)")
    
    # Check sentence length
    long_sentences = [s for s in sentences if len(s.split()) > 40]
    if len(long_sentences) > 3:
        score -= 10
        issues.append(f"{len(long_sentences)} sentences too long (> 40 words)")
    
    return {
        "score": max(score, 0),
        "words": len(words),
        "sentences": len([s for s in sentences if s.strip()]),
        "issues": issues,
        "quality": "excellent" if score >= 80 else "acceptable" if score >= 60 else "needs improvement"
    }

# ─────────────────────────────────────────
# AGENT
# ─────────────────────────────────────────
generation_agent = Agent(
    name=AGENT_NAME,
    model="gpt-5.4-mini",
    instructions=f"""You are an expert writer who generates high-quality technical content.

You write in {LANGUAGE} with a {STYLE} style for {AUDIENCE}.

Generation process:
1. Analyze the brief (type, subject, audience, length, required points)
2. Write the content following the requested format:
   - article -> hook -> 3-5 sections -> conclusion + CTA
   - email -> subject line -> context -> clear request -> signature
   - documentation -> description -> installation -> usage -> examples -> FAQ
   - report -> executive summary -> analysis -> recommendations
   - readme -> badges -> description -> installation -> usage -> contribution
3. Evaluate quality with evaluate_content()
4. If the score < 70, improve and re-evaluate
5. Save the final result

Inviolable rules:
- Zero repetition of ideas between sections
- Each section brings new value
- Include at least one concrete example (code or real case) per important section
- Get to the point from the first sentence""",
    tools=[save_content, evaluate_content],
)

# ─────────────────────────────────────────
# MAIN INTERFACE
# ─────────────────────────────────────────
async def generate(brief: ContentBrief) -> str:
    """Generate content from a structured brief."""
    
    # Convert the brief to a natural language instruction
    points = ""
    if brief.required_points:
        points = f"\nRequired points to cover:\n" + "\n".join([f"- {p}" for p in brief.required_points])
    
    sizes = {"court": "300-500 mots", "moyen": "600-900 mots", "long": "1000-1500 mots"}
    
    instruction = f"""Generate a {brief.type} on the subject: {brief.subject}

Target audience: {brief.audience}
Length: {sizes[brief.length]}
Tone: {brief.tone}
{points}

Save the final content in Markdown format."""
    
    result = await Runner.run(generation_agent, input=instruction, max_turns=10)
    return result.final_output

async def main():
    """Template demo."""
    
    brief = ContentBrief(
        type="article",
        subject="Pourquoi utiliser l'OpenAI Agents SDK plutôt que LangChain en 2026",
        length="moyen",
        tone="neutre",
        required_points=[
            "Comparaison des deux approches sur la simplicité",
            "Cas où LangChain reste pertinent",
            "Exemple de code concret avec le SDK",
        ]
    )
    
    print(f"Generating a {brief.type} on: {brief.subject}\n")
    result = await generate(brief)
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
