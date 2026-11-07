# Errata — écarts entre le livre et ce repo

Le code de ce repo est extrait du livre puis testé. Voici ce qui diffère.

## Corrections

Aucune : le code du livre tourne tel quel.

## Fichiers ajoutés par le repo

- `day3/cost_calculator.py` — version complète du script (le livre en montre une version condensée au §3.5)
- `templates/template_research_agent.py` — code complet (le livre en montre le plan et un extrait)
- `templates/template_agent_generation.py` — code complet (le livre en montre le plan et un extrait)
- `templates/template_orchestrator_agent.py` — code complet (le livre en montre le plan et un extrait)
- `bonus_from_scratch/multi_agent.py` — code complet du §B.7 (le livre en montre le plan et un extrait)
- `bonus_from_scratch/agent_complet.py` — code complet du §B.8 (le livre en montre le plan et un extrait)
- `day5/my_pipeline.py` — `process_request()` importé par `tests/test_pipeline.py`
- `day5/my_agents.py` — `billing_agent` importé par `tests/test_golden.py` et `tests/test_snapshot.py`
- `day5/tests/__snapshots__/test_snapshot.ambr` — snapshot de référence (séquence d'outils), pour que `pytest tests/` passe sans `--snapshot-update`
- `day5/pytest.ini` — `pythonpath` pour `from tools.vat import ...` + boucle asyncio partagée entre les tests
