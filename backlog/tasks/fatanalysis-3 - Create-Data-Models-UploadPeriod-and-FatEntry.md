---
id: FATANALYSIS-3
title: Create Data Models (UploadPeriod and FatEntry)
status: Done
assignee: []
created_date: '2026-07-31 16:52'
updated_date: '2026-07-31 17:05'
labels: []
dependencies: []
ordinal: 3000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Definieer de database modellen in Django voor het opslaan van FAT periodes en individuele speler records.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Model UploadPeriod aangemaakt met velden: upload datum, uploader, type (30 of 90 dagen).
- [x] #2 Model FatEntry aangemaakt met velden: koppeling met UploadPeriod, speler/karakter (Alliance Auth character), FAT data.
- [x] #3 Migraties kunnen succesvol en zonder fouten doorgevoerd worden.
- [x] #4 Het 'FatEntry' model slaat de specifieke fleet types (Strategic, QRF, Astartes etc.) flexibel op, bijvoorbeeld met een JSONField, zodat wisselende kolommen in CSV bestanden ondersteund worden zonder hardcoded velden.
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Created UploadPeriod and FatEntry models. JSONField added for dynamic fleet type tracking. Migrations generated successfully.
<!-- SECTION:NOTES:END -->
