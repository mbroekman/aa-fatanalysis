---
id: FATANALYSIS-5
title: Build CSV Import Functionality
status: Done
assignee: []
created_date: '2026-07-31 16:52'
updated_date: '2026-07-31 17:06'
labels: []
dependencies: []
ordinal: 5000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Ontwikkel de backend logica en het frontend formulier voor het uploaden, parsen en inlezen van de CSV bestanden.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Er is een UI formulier om een CSV bestand te selecteren en de import type (30 of 90 dagen) te kiezen.
- [x] #2 De backend kan de CSV correct uitlezen en verwerken (mapping met Alliance Auth karakters).
- [x] #3 Bij een succesvolle upload wordt er een UploadPeriod record aangemaakt inclusief de bijbehorende FatEntry records.
- [x] #4 Er is duidelijke foutafhandeling wanneer de CSV corrupt of ongeldig is.
- [x] #5 De importlogica leest de CSV headers dynamisch uit en bewaart alle kolommen die niet tot de standaard gebruikersinfo behoren, als extra FAT-data (bijv. in de JSONField structuur).
- [x] #6 De import functionaliteit verwerkt correct de extra kolommen die voorkomen in het 90 dagen overzicht ten opzichte van de 30 dagen.
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Implemented CSV Import view with dynamic column parsing into JSONField.
<!-- SECTION:NOTES:END -->
