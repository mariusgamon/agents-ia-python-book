import logging

log = logging.getLogger(__name__)


def apply_vllm_strict_field_workaround() -> None:
    """
    Strip the `strict` field from function tool payloads sent to the model.

    Some OpenAI-compatible servers (older vLLM, custom gateways) reject this
    field with a Pydantic validation error. The SDK injects it automatically,
    so we patch the converter to remove it after serialization.

    Trade-off: we lose the strict-mode JSON schema enforcement, but vLLM
    doesn't support that anyway, so net zero on this stack.

    WARNING: this patches an internal SDK API and may break on upgrades.
    Cover it with an integration test (see scenario 0 below).
    """
    try:
        from agents.models.chatcmpl_converter import Converter

        if getattr(Converter, "_vllm_strict_patched", False):
            return  # idempotent

        _orig = Converter.tool_to_openai.__func__

        @classmethod
        def _patched(cls, tool):
            result = _orig(cls, tool)
            if isinstance(result, dict):
                func = result.get("function")
                if isinstance(func, dict):
                    func.pop("strict", None)
            return result

        Converter.tool_to_openai = _patched
        Converter._vllm_strict_patched = True
        log.info("vllm_compat: stripped 'strict' field from function_tool payloads")
    except Exception as e:
        log.warning("vllm_compat: patch failed: %s", e)
