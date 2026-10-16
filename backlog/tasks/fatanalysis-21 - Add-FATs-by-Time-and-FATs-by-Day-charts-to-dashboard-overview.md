---
id: FATANALYSIS-21
title: Add FATs by Time and FATs by Day charts to dashboard overview
status: Done
assignee: []
created_date: '2026-10-16 16:57'
updated_date: '2026-10-16 17:05'
labels: []
dependencies: []
priority: high
type: feature
ordinal: 21000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Scrape and ingest hourly and weekday distribution metrics from INIT Auth statistics pages ('time-line' and 'weekday-line' charts) into FatMonthPeriod. Aggregate these across dynamic time windows in FatAggregationService and render interactive 'FATs by Time (EVE Time)' and 'FATs by Day (Weekday)' charts on the main dashboard.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Add fats_by_time and fats_by_weekday JSON fields to FatMonthPeriod model with database migration
- [ ] #2 Parse time-line and weekday-line dataset values in AfatScraperService / FatIngestionService
- [ ] #3 Aggregate hourly (0-23) and weekday (Mon-Sun) distributions across active periods in FatAggregationService
- [ ] #4 Render 'FATs by Time' and 'FATs by Day' responsive charts on index.html overview and period_detail.html
- [ ] #5 All tests pass cleanly and new unit tests verify chart ingestion and window aggregation
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added fats_by_time (24-hour hourly distribution) and fats_by_weekday (7-day weekday distribution) JSON fields to FatMonthPeriod (migration 0005). Added parser in FatIngestionService to scrape time-line and weekday-line datasets from INIT Auth HTML. Aggregated distributions across dynamic windows in FatAggregationService and rendered interactive Chart.js line and bar charts on index.html and period_detail.html.
<!-- SECTION:FINAL_SUMMARY:END -->
