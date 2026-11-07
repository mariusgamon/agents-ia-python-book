# app/middleware/agent_metrics.py — lightweight agent-specific monitoring
import os
import time
import json
import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path

logger = logging.getLogger("agent.metrics")

@dataclass
class RunMetrics:
    """Capture tout ce que le health check standard rate."""
    run_id: str = ""
    llm_calls: int = 0
    llm_total_ms: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    tool_calls: int = 0
    tool_failures: int = 0
    tool_names: list = field(default_factory=list)
    max_turns_hit: bool = False
    stuck_detected: bool = False  # same tool called 3+ times consecutively
    
    def record_llm_call(self, duration_ms: int, in_tokens: int, out_tokens: int):
        self.llm_calls += 1
        self.llm_total_ms += duration_ms
        self.input_tokens += in_tokens
        self.output_tokens += out_tokens
    
    def record_tool_call(self, tool_name: str, success: bool):
        self.tool_calls += 1
        self.tool_names.append(tool_name)
        if not success:
            self.tool_failures += 1
        # Détection de blocage : même outil 3+ fois d'affilée
        if len(self.tool_names) >= 3 and len(set(self.tool_names[-3:])) == 1:
            self.stuck_detected = True
            logger.warning(f"Stuck agent detected: {tool_name} called 3x consecutively",
                         extra={"run_id": self.run_id, "tool_name": tool_name})
    
    @property
    def estimated_cost_usd(self) -> float:
        # Prices come from env vars so you can update without redeploying.
        # IMPORTANT: these are indicative — verify the official OpenAI pricing
        # page for your model (rates differ for gpt-5.4, gpt-5.4-mini, gpt-6-luna, etc.)
        input_price = float(os.getenv("MODEL_INPUT_COST_PER_1M", "2.50"))
        output_price = float(os.getenv("MODEL_OUTPUT_COST_PER_1M", "10.00"))
        return (self.input_tokens * input_price + self.output_tokens * output_price) / 1_000_000
    
    def to_log_line(self) -> str:
        return json.dumps(asdict(self))

def emit_run_metrics(metrics: RunMetrics):
    """Log les métriques en JSON structuré + append dans un fichier JSONL local."""
    logger.info(
        f"run completed: {metrics.llm_calls} LLM calls, "
        f"{metrics.input_tokens + metrics.output_tokens} tokens, "
        f"${metrics.estimated_cost_usd:.4f}",
        extra={
            "run_id": metrics.run_id,
            "llm_calls": metrics.llm_calls,
            "token_count": metrics.input_tokens + metrics.output_tokens,
            "tool_failures": metrics.tool_failures,
            "stuck_detected": metrics.stuck_detected,
            "cost_usd": metrics.estimated_cost_usd,
        }
    )
    # Écriture dans un fichier local — persistance légère, rotation avec logrotate
    metrics_file = Path("agent_metrics.jsonl")
    with open(metrics_file, "a") as f:
        f.write(metrics.to_log_line() + "\n")
