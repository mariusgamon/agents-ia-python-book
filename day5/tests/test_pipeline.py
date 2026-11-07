# tests/test_pipeline.py
from unittest.mock import patch, MagicMock
import pytest
from my_pipeline import process_request  # votre code qui appelle Runner.run()

@pytest.mark.asyncio
async def test_process_request_handles_empty_output():
    fake_result = MagicMock()
    fake_result.final_output = ""  # cas pathologique : agent muet
    fake_result.raw_responses = []

    with patch("my_pipeline.Runner.run", return_value=fake_result):
        response = await process_request("bonjour")

    assert response["status"] == "empty_response"
    assert response["fallback_used"] is True
