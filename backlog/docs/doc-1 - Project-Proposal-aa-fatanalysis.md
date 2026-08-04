---
id: doc-1
title: 'Project Proposal: aa-fatanalysis'
type: guide
created_date: '2026-07-31 16:52'
updated_date: '2026-07-31 16:53'
---
# Voorstel: aa-fatanalysis

Dit is het voorstel voor de nieuwe Alliance Auth applicatie **aa-fatanalysis** (FAT Analysis). Deze applicatie zal zich richten op het importeren, beheren en visualiseren van FAT (Fleet Activity Tracking) gegevens.

## 1. Doel van de Applicatie
Het eenvoudig inzichtelijk maken van de FAT-registraties voor zowel individuele spelers als corporaties binnen Alliance Auth, op basis van CSV-uploads.

## 2. Kernfunctionaliteiten

### 2.1. CSV Import & Periodebeheer
- **Uploadfunctionaliteit:** Mogelijkheid om CSV-bestanden te uploaden.
- **Import Types:** Keuze tussen een import van **30 dagen** of **90 dagen**.
- **Periodes:** Elke upload wordt in het systeem geregistreerd als een unieke 'periode'.
- **Overzicht Uploads:** Een overzichtsscherm met alle geüploade bestanden/periodes.
- **Verwijderen (Rollback):** Mogelijkheid om een specifieke upload (periode) volledig te verwijderen, inclusief alle daaraan gekoppelde data.

### 2.2. Overzichten & Dashboards
- **Algemeen Totaaloverzicht:** Een overzicht voor het management van alle FAT's over de actieve 30- en 90-dagen periodes.
- **Spelersoverzicht:** Specifiek overzicht per speler waarin duidelijk hun FAT-aantallen voor de 30- en 90-dagen periodes staan weergegeven.

### 2.3. Visualisaties (Grafieken)
- **Corporatie Niveau:** Grafieken die de trend en activiteit van de corporatie per periode (upload) visualiseren.
- **Speler Niveau:** Grafieken die de FAT-activiteit van een specifieke speler over de verschillende periodes inzichtelijk maken.

## 3. Technisch Concept (Django / Alliance Auth)
- **Modellen:**
  - `UploadPeriod`: Slaat metadata op over de upload (datum, type (30/90), uploader).
  - `FatEntry`: Individuele records uit de CSV, gekoppeld aan een `UploadPeriod` en een `User/Character`.
- **Frontend:** Standaard Alliance Auth styling (Bootstrap) gecombineerd met een grafiekenbibliotheek zoals **Chart.js** voor de visuele weergave.
