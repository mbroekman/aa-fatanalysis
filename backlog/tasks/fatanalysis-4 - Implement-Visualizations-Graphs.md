---
id: FATANALYSIS-4
title: Implement Visualizations (Graphs)
status: Done
assignee: []
created_date: '2026-07-31 16:52'
updated_date: '2026-07-31 17:07'
labels: []
dependencies: []
ordinal: 4000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Integreer een grafiekenbibliotheek (zoals Chart.js) om de activiteit visueel weer te geven per upload periode op corporatie- en spelersniveau.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Op corporatie niveau is er een grafiek die de fluctuatie / trend van de FAT activiteit over verschillende periodes (uploads) toont.
- [x] #2 Als men een specifieke speler bekijkt, is er een grafiek die de persoonlijke activiteit van deze speler toont over opeenvolgende periodes.
- [x] #3 De grafieken laden snel en passen zich correct aan het Alliance Auth donkere/lichte thema aan indien van toepassing.
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Added period_detail view with Chart.js pie and bar charts for Corp and Player FAT breakdowns.
<!-- SECTION:NOTES:END -->
