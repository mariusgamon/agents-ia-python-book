# dev_orchestrator.py
import config

from agents import Agent, Runner, function_tool, handoff
import subprocess
import asyncio
from pathlib import Path

# ⚠️ VERSION VOLONTAIREMENT DANGEREUSE (démonstration) : shell=True + commande écrite par le LLM.
# Ne la copiez pas : utilisez execute_safe_command, avec sa liste blanche, juste après.
@function_tool
def execute_command(command: str, directory: str = ".") -> dict:
    """
    Executes a shell command in a given directory.
    
    Args:
        command: The command to execute (e.g., "git status", "pytest tests/")
        directory: The working directory
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=directory,
            timeout=60
        )
        return {
            "returncode": result.returncode,
            "stdout": result.stdout[:2000],
            "stderr": result.stderr[:500],
            "success": result.returncode == 0
        }
    except subprocess.TimeoutExpired:
        return {"error": "Timeout — command took too long", "success": False}
    except Exception as e:
        return {"error": str(e), "success": False}

# Sandbox the agent's file access to a workspace directory.
# Without this, an LLM could ask to read /etc/passwd or .env, or
# write outside the project. Indirect prompt injection (a tool reading
# a malicious file/diff/issue) makes this dangerous even in internal use.
WORKSPACE = Path.cwd().resolve()

def resolve_workspace_path(filepath: str) -> Path:
    """Resolve filepath under WORKSPACE; reject anything escaping it."""
    candidate = (WORKSPACE / filepath).resolve()
    try:
        candidate.relative_to(WORKSPACE)
    except ValueError:
        raise PermissionError(f"Path outside workspace is not allowed: {filepath}")
    return candidate

@function_tool
def read_file(filepath: str) -> str:
    """Reads the contents of a file under the workspace directory."""
    try:
        path = resolve_workspace_path(filepath)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return content[:5000]  # Max 5000 characters
    except FileNotFoundError:
        return f"File not found: {filepath}"
    except PermissionError as e:
        return f"Refused: {e}"

@function_tool
def write_file(filepath: str, content: str) -> str:
    """Writes content to a file under the workspace directory."""
    try:
        path = resolve_workspace_path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"File written: {path.relative_to(WORKSPACE)} ({len(content)} characters)"
    except PermissionError as e:
        return f"Refused: {e}"
    except Exception as e:
        return f"Write error: {e}"

# Specialized agent: tests
test_agent = Agent(
    name="TestAgent",
    model=config.DEFAULT_MODEL,
    instructions="""You generate pytest tests for Python code.
    For each function or class, you create:
    - A nominal case test (happy path)
    - A boundary value test
    - An expected error test
    You use fixtures when appropriate.
    The test code must be immediately runnable.""",
    tools=[read_file, write_file, execute_command],
)

# Specialized agent: changelog
changelog_agent = Agent(
    name="ChangelogAgent",
    model=config.DEFAULT_MODEL,
    instructions="""You maintain a CHANGELOG.md file following the Keep a Changelog format.
    You read the latest git commits, group them by category (Added, Changed, Fixed, etc.)
    and add a new section for the requested version.""",
    tools=[read_file, write_file, execute_command],
)

# Specialized agent: PR description
pr_agent = Agent(
    name="PRAgent",
    model=config.DEFAULT_MODEL,
    instructions="""You generate clear and comprehensive Pull Request descriptions.
    You analyze the git diff, understand the changes, and write:
    - A concise title
    - A summary in 3 bullets
    - Tests to perform
    - Potential risks""",
    tools=[execute_command],
)

# The orchestrator
orchestrator = Agent(
    name="DevOrchestrator",
    model=config.DEFAULT_MODEL,
    instructions="""You are a senior development assistant.
    You route incoming requests to a single specialized agent that can
    answer alone:
    - Test-related requests → TestAgent
    - Changelog updates    → ChangelogAgent
    - PR descriptions      → PRAgent

    Pick exactly one. The chosen agent owns the answer end-to-end —
    you do not collect its output to compose a follow-up.""",
    handoffs=[
        handoff(test_agent),
        handoff(changelog_agent),
        handoff(pr_agent),
    ],
)

async def main():
    requests = [
        "Generate tests for the file app/agents/assistant.py",
        "Update the CHANGELOG for version 1.1.0 with this week's commits",
        "Generate a PR description for my latest git changes",
    ]
    
    for request in requests:
        print(f"\n{'='*50}")
        print(f"Request: {request}")
        print('='*50)
        
        result = await Runner.run(orchestrator, input=request)
        print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
