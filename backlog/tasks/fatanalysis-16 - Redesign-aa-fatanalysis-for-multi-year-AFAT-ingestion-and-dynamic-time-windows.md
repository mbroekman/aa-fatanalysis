---
id: FATANALYSIS-16
title: Redesign aa-fatanalysis for multi-year AFAT ingestion and dynamic time windows
status: Done
assignee: []
created_date: '2026-10-16 10:21'
updated_date: '2026-10-16 13:20'
labels: []
dependencies: []
priority: high
type: feature
ordinal: 16000
---

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Design new data models for monthly corp and character FAT tracking without legacy 30/90 hardcoding
- [x] #2 Implement service layer to scrape and ingest multi-year FAT data from INIT Auth AFAT via session cookie
- [x] #3 Build frontend management UI for directors to configure and trigger data synchronization
- [x] #4 Implement dynamic aggregation supporting 30, 90, 120 days, YTD, and multi-year time windows
- [x] #5 Modernize all templates to strict Bootstrap 5 standards
- [x] #6 Add comprehensive unit tests for scraper, models, services, and views
<!-- AC:END -->
