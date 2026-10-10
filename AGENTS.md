# AA-FATAnalysis (Fleet Activity Tracking) - AI Agent Guidelines

Dit project maakt integraal onderdeel uit van de Workbench 001 workspace en erft alle bindende richtlijnen van het centrale hoofd-instructiedocument:
👉 **[Centrale AGENTS.md](file:///g:/My%20Drive/Workbench%20001/AGENTS.md)**

Lees tevens altijd eerst [.agent/memory.md](file:///g:/My%20Drive/Workbench%20001/.agent/memory.md) vóór analyse of modificatie (Regel 1 van AGENTS.md).

---

## 1. Project Context & Backlog Directory

- **Plugin:** `aa-fatanalysis` (Django App: `fatanalysis`)
- **Backlog Map:** `plugins/aa-fatanalysis/backlog/`
- **Directory Context (CRITICAL):** Alle `backlog` CLI commando's en MCP interacties **MOETEN** worden uitgevoerd met de werkmap ingesteld op `plugins/aa-fatanalysis` (bijv. `cd plugins/aa-fatanalysis` of via de `Cwd` parameter in toolcalls), zodat taken correct in de backlog van `aa-fatanalysis` worden geplaatst en beheerd.

---

## 2. Bindende Centrale Regels (Inherited from Master AGENTS.md)

Alle standaarden uit de centrale [AGENTS.md](file:///g:/My%20Drive/Workbench%20001/AGENTS.md) zijn hier onverkort van toepassing:

- **Taakbeheer via Backlog.md:** Eerst taak registreren/WIP zetten in `backlog-md` vóór het schrijven of wijzigen van code. Afronden pas na testen, linting en type-checks.
- **Tooling & Omgeving:** `uv` voor package management, `Ruff` (line-length 120), `mypy` strict met `django-stubs`, `pytest` en `pytest-django`.
- **Alliance Auth UI & Bootstrap 5:** Altijd `{% extends "allianceauth/base-bs5.html" %}`, uitsluitend Bootstrap 5 componenten (`card`, `badge bg-*`, `d-flex`, `btn-sm`). Nooit Bootstrap 3 componenten (`panel`, `label`, `pull-right`). Geen eigen `{% if messages %}` block toevoegen.
- **Pre-Commit Verificatie:** Update `CHANGELOG.md` en user docs vóór taakafronding. Nooit automatische releases of tags.
