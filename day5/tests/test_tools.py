# tests/test_tools.py
# On teste la logique (compute_vat, fetch_weather), pas les objets FunctionTool.
import pytest
from tools.vat import compute_vat
from tools.weather import fetch_weather

# --- Tests déterministes (pas de LLM, pas d'API externe) ---

def test_vat_standard_rate():
    result = compute_vat(1000, rate=0.20)
    assert result["vat_amount"] == 200.0
    assert result["amount_incl_tax"] == 1200.0

def test_vat_zero_amount():
    result = compute_vat(0)
    assert result["vat_amount"] == 0.0

def test_vat_custom_rate():
    result = compute_vat(1000, rate=0.055)
    assert result["vat_amount"] == 55.0

# --- Tests avec mock (API externe simulée) ---

@pytest.mark.asyncio
async def test_weather_api_down(monkeypatch):
    """Quand l'API météo est indisponible, l'outil retourne une erreur propre."""
    import httpx

    async def mock_get(*args, **kwargs):
        raise httpx.ConnectTimeout("API unreachable")

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)
    result = await fetch_weather("Paris")
    assert "error" in result
    assert "timeout" in result["error"].lower()
