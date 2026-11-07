# observe_with_logfire.py — instrumentation automatique
import logfire
import openai
from dotenv import load_dotenv

load_dotenv()                          # charge LOGFIRE_TOKEN et OPENAI_API_KEY depuis .env
logfire.configure()
logfire.instrument_openai()            # ← capture tous les appels OpenAI

# À partir de là, chaque appel SDK génère une trace dans Logfire
# Aucune modification de votre code agent nécessaire
