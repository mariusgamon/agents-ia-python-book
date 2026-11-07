# safe_retry.py — same job, 10x cheaper when things go wrong
# pip install backoff
import config

import asyncio
import backoff
from agents import Agent, Runner
from openai import RateLimitError, APIStatusError

class BudgetExhaustedError(RuntimeError):
    """Raised when the global token budget is exceeded."""

agent = Agent(
    name="BatchProcessor",
    instructions="You rewrite product descriptions for SEO.",
    model="gpt-5.4",
)

class TokenBudget:
    """Global budget guard — kills the pipeline before the bill explodes."""
    def __init__(self, max_tokens: int):
        self.max_tokens = max_tokens
        self.used = 0
        self._lock = asyncio.Lock()

    async def consume(self, tokens: int):
        async with self._lock:
            self.used += tokens
            if self.used > self.max_tokens:
                raise BudgetExhaustedError(
                    f"Budget exceeded: {self.used:,}/{self.max_tokens:,} tokens. "
                    f"Estimated cost: ${self.used / 1_000_000 * BLENDED_COST_PER_1M:.2f}"
                )

# Blended cost estimate (volontairement simplifié — le vrai coût dépend du
# modèle, du ratio input/output, et de la tarification courante OpenAI).
# Pour un calcul exact, séparez input_tokens et output_tokens.
BLENDED_COST_PER_1M = 6.25  # USD, blended estimate

# Hard ceiling: 5M tokens × $6.25/M ≈ $31.25 max (with this blended rate)
budget = TokenBudget(max_tokens=5_000_000)

def extract_tokens(result) -> int:
    """Pull total token usage across the entire run (multi-tour, multi-tool aggregated)."""
    try:
        # context_wrapper.usage aggregates ALL LLM calls of the run
        # (tool calls, handoffs, multi-turn). raw_responses[-1] would only
        # capture the last response and miss everything before.
        return result.context_wrapper.usage.total_tokens
    except AttributeError:
        return 0  # fallback — don't crash the pipeline on a missing metric

def is_non_retriable(exc):
    """Don't retry deterministic 4xx errors (400/401/403/404/422).
    Only retry RateLimitError (429) and transient 5xx server errors."""
    if isinstance(exc, APIStatusError):
        return exc.status_code not in (500, 502, 503, 504)
    return False  # RateLimitError is always retriable

@backoff.on_exception(
    backoff.expo,
    (RateLimitError, APIStatusError),
    max_tries=3,            # finite retries — fail fast, requeue later
    max_value=60,           # cap delay at 60s even on later retries
    jitter=backoff.full_jitter,
    giveup=is_non_retriable,  # 4xx errors abort immediately
)
async def process_document(document: str) -> str:
    """Retry transient errors (429, 5xx) with backoff; abort on 4xx; track budget."""
    result = await Runner.run(agent, input=document, max_turns=5)
    await budget.consume(extract_tokens(result))
    return result.final_output

async def main():
    docs = [
        "Red running shoes, breathable mesh, size 42.",
        "Wireless headphones, 30h battery, noise cancellation.",
        "Leather wallet, 6 card slots, minimalist design.",
    ]
    for doc in docs:
        try:
            seo_desc = await process_document(doc)
            print(f"\n→ {doc}\n✓ {seo_desc}\n")
        except BudgetExhaustedError as e:
            print(f"⛔ {e}")
            break  # stop the batch — investigate before resuming
    print(f"Budget used: {budget.used:,} / {budget.max_tokens:,} tokens")

if __name__ == "__main__":
    asyncio.run(main())
