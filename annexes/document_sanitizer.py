# document_sanitizer.py — strip hidden-text tricks and known injection phrases
import re
from typing import Iterable

# Patterns qui n'ont rien à faire dans un document utilisateur légitime
SUSPICIOUS_PHRASES = [
    r"ignore\s+(all\s+|toutes?\s+)?(previous|précédentes?)\s+instructions?",
    r"(you\s+are|tu\s+es)\s+now\s+(a|an|un|une)",
    r"(system|assistant)\s*:\s*new\s+instructions?",
    r"\bsend_email\b|\bwebhook\b|\bcurl\b|\bexec\b",
    r"sk-[a-zA-Z0-9]{20,}",  # clés API dans le document
]
SUSPICIOUS_REGEX = re.compile("|".join(SUSPICIOUS_PHRASES), re.IGNORECASE)

def sanitize_document(raw_text: str) -> tuple[str, list[str]]:
    """Clean a document and report what was stripped.

    Returns (cleaned_text, list_of_findings).
    Findings non vide => traitez avec suspicion (refus, validation humaine, etc.).
    """
    findings = []

    # 1. Supprimer les caractères de contrôle invisibles (zero-width, RTL override)
    cleaned = re.sub(r"[\u200B-\u200F\u202A-\u202E\uFEFF]", "", raw_text)

    # 2. Supprimer les blocs de markup qui n'ont aucune raison d'y être
    cleaned = re.sub(r"</?(system|assistant|instruction)[^>]*>", "", cleaned,
                     flags=re.IGNORECASE)

    # 3. Repérer les phrases d'injection — on ne les supprime PAS (on veut savoir),
    #    on logue et on laisse le caller décider
    for match in SUSPICIOUS_REGEX.finditer(cleaned):
        findings.append(match.group()[:80])

    return cleaned, findings

# Usage
raw = extract_text_from_pdf("cv_candidate.pdf")
clean, findings = sanitize_document(raw)
if findings:
    logger.warning("Injection-like patterns in document", extra={"findings": findings})
    # Politique produit : on refuse, on escalade, ou on continue avec un modèle classifier ?
    raise DocumentRejected(f"Suspicious content: {findings[:3]}")

safe_input = f"Résume ce CV :\n<document>{clean}</document>"
result = await Runner.run(cv_agent, input=safe_input)
