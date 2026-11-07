# sprint_report.py
import config

from agents import Agent, Runner, function_tool
import httpx
import json
import asyncio
import os
from pathlib import Path

@function_tool
async def get_github_prs(repo: str, since_days: int = 7) -> list[dict]:
    """
    Récupère les Pull Requests récemment mergées d'un repo GitHub.

    Args:
        repo: Format "owner/repo" (ex: "my-org/my-project")
        since_days: Nombre de jours à remonter (cutoff en UTC)
    """
    from datetime import datetime, timedelta, timezone

    token = os.getenv("GITHUB_TOKEN")
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    # Use timezone-aware UTC — GitHub returns ISO 8601 with 'Z' (= UTC).
    # Mixing naive datetime.now() with a "Z" suffix would compare apples to pears.
    cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)

    def parse_github_date(value: str) -> datetime:
        # GitHub dates: "2026-04-22T14:03:11Z" — Python's fromisoformat does
        # not accept the trailing 'Z' before 3.11, so normalize it.
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    async with httpx.AsyncClient(timeout=15.0) as client:
        # Note: per_page max is 100. For very active repos with hundreds of
        # PRs in `since_days`, paginate via the `page` parameter and stop
        # when you hit a PR older than `cutoff`. Kept simple here for clarity.
        resp = await client.get(
            f"https://api.github.com/repos/{repo}/pulls",
            headers=headers,
            params={"state": "closed", "sort": "updated", "direction": "desc", "per_page": 100},
        )

        if resp.status_code != 200:
            return [{"error": f"GitHub API {resp.status_code}"}]

        prs = resp.json()
        recent_prs = [
            {
                "number":      pr["number"],
                "title":       pr["title"],
                "author":      pr["user"]["login"],
                "merged_at":   pr["merged_at"],
                "description": (pr["body"] or "")[:200],
            }
            for pr in prs
            if pr.get("merged_at") and parse_github_date(pr["merged_at"]) >= cutoff
        ]

        return recent_prs

import re

REPORTS_DIR = Path("reports").resolve()

def safe_filename(name: str) -> str:
    """Strip anything that's not a-zA-Z0-9_-, cap at 80 chars.
    Prevents path traversal (../../etc/passwd) and weird chars from the LLM."""
    cleaned = re.sub(r"[^a-zA-Z0-9_-]", "_", name)
    return cleaned[:80] or "report"

@function_tool
def save_report(content: str, filename: str) -> str:
    """
    Sauvegarde le rapport dans un fichier Markdown sous reports/.

    Args:
        content: Contenu du rapport en Markdown
        filename: Nom du fichier (sans extension) — sera nettoyé pour
                  éviter les caractères dangereux et le path traversal.
    """
    REPORTS_DIR.mkdir(exist_ok=True)
    safe_name = safe_filename(filename)
    filepath = (REPORTS_DIR / f"{safe_name}.md").resolve()

    # Defense in depth: ensure the resolved path stays under REPORTS_DIR
    if REPORTS_DIR not in filepath.parents and filepath.parent != REPORTS_DIR:
        return "Error: filename produces a path outside the reports/ directory"

    filepath.write_text(content, encoding="utf-8")
    return f"Rapport sauvegardé : {filepath.name}"

report_agent = Agent(
    name="ReportAgent",
    model=config.DEFAULT_MODEL,
    instructions="""You generate clear and actionable sprint reports.

For each sprint report:
1. Retrieve the merged PRs of the week
2. Group them by theme (features, bugfixes, refactoring, docs)
3. Identify the main contributors
4. Calculate the volume (number of PRs per category)
5. Generate a structured Markdown report with:
   - Executive summary (3 lines max)
   - Contributions table by developer
   - List of changes by category
   - Points of attention (if a PR seems major or risky)
6. Save the report

Be factual. Do not invent information that is not in the data.""",
    tools=[get_github_prs, save_report],
)

async def generate_sprint_report(repo: str):
    from datetime import datetime
    
    result = await Runner.run(
        report_agent,
        input=f"""Generate the sprint report for the repo {repo}.
        Period: last 7 days.
        Filename: sprint_{datetime.now().strftime('%Y-%m-%d')}""",
        max_turns=8,
    )
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(generate_sprint_report("your-org/your-repo"))
