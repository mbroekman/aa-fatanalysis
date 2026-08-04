---
id: FATANALYSIS-6
title: Implement Upload & Period Management
status: Done
assignee: []
created_date: '2026-07-31 16:52'
updated_date: '2026-07-31 17:08'
labels: []
dependencies: []
ordinal: 6000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Voeg een beheerscherm toe waar gebruikers een overzicht kunnen zien van alle eerdere CSV uploads, inclusief de mogelijkheid om een foute/oude periode veilig te verwijderen en daarmee de gekoppelde data te verwijderen (rollback).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Er is een overzichtspagina beschikbaar van alle verwerkte bestanden / periodes.
- [x] #2 Gebruikers met de juiste rechten kunnen op een 'Verwijder' knop klikken naast een periode.
- [x] #3 Bij het verwijderen van een periode wordt het UploadPeriod record inclusief álle daaraan gekoppelde FatEntry records succesvol en permanent verwijderd uit de database.
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Added period_list and period_delete views for managing and removing upload periods and all their data.
<!-- SECTION:NOTES:END -->
