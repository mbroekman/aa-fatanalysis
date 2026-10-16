---
id: FATANALYSIS-22
title: >-
  Transform Fleet Types chart into Ship Types Breakdown using INIT Auth ship
  statistics
status: Done
assignee: []
created_date: '2026-10-16 17:12'
labels: []
dependencies: []
priority: high
type: feature
ordinal: 22000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Scrape and ingest corporation ship statistics from INIT Auth monthly reports ('ship-bar-stacked' dataset) into FatMonthPeriod.fats_by_ship. Dynamically aggregate ship distributions across the active time window in FatAggregationService and render an interactive 'Ship Types Breakdown' doughnut chart on the dashboard overview.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Add fats_by_ship JSON field to FatMonthPeriod model with database migration
- [x] #2 Extract ship-bar-stacked dataset in FatIngestionService.parse_html_charts
- [x] #3 Aggregate ship distribution across active time windows in FatAggregationService
- [x] #4 Update index.html template and Chart.js to render 'Ship Types Breakdown' doughnut chart
- [x] #5 Add regression tests and backfill existing devauth periods
<!-- AC:END -->
