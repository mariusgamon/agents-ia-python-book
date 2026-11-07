# email_extractor.py
import config
from pydantic import BaseModel, Field
from agents import Agent, Runner
import asyncio


class ActionItem(BaseModel):
    """Une action à réaliser extraite de l'email."""
    description: str = Field(description="Description courte de l'action")
    assignee: str | None = Field(
        default=None,
        description="Personne à qui l'action est assignée, si mentionnée"
    )


class EmailAnalysis(BaseModel):
    """Analyse structurée d'un email entrant."""
    sender_name: str = Field(description="Nom complet de l'expéditeur")
    sender_company: str | None = Field(
        default=None,
        description="Entreprise de l'expéditeur, si mentionnée"
    )
    subject_summary: str = Field(
        description="Résumé du sujet en une phrase (max 15 mots)"
    )
    urgency: str = Field(
        description="Niveau d'urgence : low, medium, high, critical"
    )
    action_items: list[ActionItem] = Field(
        default_factory=list,
        description="Liste des actions demandées dans l'email"
    )
    requires_response: bool = Field(
        description="True si l'email attend une réponse explicite"
    )


agent = Agent(
    name="EmailAnalyzer",
    model=config.DEFAULT_MODEL,
    instructions="""You analyze incoming emails and extract structured information.
    Be precise and concise. For urgency, use these rules:
    - critical: deadline within 24h or explicit "urgent"
    - high: deadline within a week or strong language
    - medium: standard business request
    - low: informational, no action needed""",
    output_type=EmailAnalysis,  # ← Force structured output
)


TEST_EMAIL = """
Bonjour,

Suite à notre appel de ce matin, je vous confirme que le déploiement
de la v2 doit impérativement être terminé avant vendredi 18h.

Le client (Acme Corp) menace de résilier le contrat si on ne livre pas
à temps. Pouvez-vous :
1. Finaliser les tests d'intégration d'ici mercredi
2. Préparer le script de migration pour Thomas
3. Me confirmer par retour de mail que c'est faisable

Merci,
Sophie Martin
Directrice Technique — DataFlow SAS
"""


async def main():
    result = await Runner.run(agent, input=TEST_EMAIL)

    # result.final_output est directement un objet EmailAnalysis
    analysis: EmailAnalysis = result.final_output

    print(f"De : {analysis.sender_name} ({analysis.sender_company})")
    print(f"Sujet : {analysis.subject_summary}")
    print(f"Urgence : {analysis.urgency}")
    print(f"Réponse attendue : {'Oui' if analysis.requires_response else 'Non'}")
    print(f"\nActions ({len(analysis.action_items)}) :")
    for i, action in enumerate(analysis.action_items, 1):
        assignee = f" → {action.assignee}" if action.assignee else ""
        print(f"  {i}. {action.description}{assignee}")

    # En production : sérialisez vers votre BDD / API
    print(f"\nJSON pour votre API :\n{analysis.model_dump_json(indent=2)}")


asyncio.run(main())
