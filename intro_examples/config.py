# config.py
from dotenv import load_dotenv
import os

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError(
        "OPENAI_API_KEY manquant dans .env. "
        "Obtenez-en une sur https://platform.openai.com/api-keys"
    )

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-5.4-mini")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
