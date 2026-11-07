from vllm_compat import apply_vllm_strict_field_workaround


def test_strict_field_stripped():
    """Verify the workaround removes the 'strict' field from tool payloads."""
    from agents import function_tool
    from agents.models.chatcmpl_converter import Converter

    apply_vllm_strict_field_workaround()

    @function_tool(strict_mode=False)
    def dummy(x: int) -> int:
        """Dummy tool for patch verification."""
        return x

    payload = Converter.tool_to_openai(dummy)
    assert "strict" not in payload.get("function", {}), \
        "Patch is broken: 'strict' field is still present"
