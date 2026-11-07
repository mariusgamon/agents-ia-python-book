# appendix/sandbox/hello_sandbox.py
import config  # Loads .env (OPENAI_API_KEY)

from agents import Runner
from agents.run import RunConfig
from agents.sandbox import Manifest, SandboxAgent, SandboxRunConfig
from agents.sandbox.entries import GitRepo
from agents.sandbox.sandboxes import UnixLocalSandboxClient

# Define a sandbox agent — same surface as a regular Agent,
# but it runs inside an isolated filesystem.
agent = SandboxAgent(
    name="Workspace Assistant",
    instructions=(
        "Inspect the sandbox workspace before answering. "
        "Use the filesystem tools to read files, do not guess."
    ),
    default_manifest=Manifest(
        entries={
            # Clones the repo into /workspace/repo inside the sandbox
            "repo": GitRepo(repo="openai/openai-agents-python", ref="main"),
        }
    ),
)

if __name__ == "__main__":
    result = Runner.run_sync(
        agent,
        "Read repo/README.md and summarize in 3 bullets what this SDK does.",
        run_config=RunConfig(
            # UnixLocalSandboxClient = runs on your local filesystem, isolated
            # For production, swap for DockerSandboxClient or a hosted provider
            sandbox=SandboxRunConfig(client=UnixLocalSandboxClient())
        ),
    )
    print(result.final_output)
