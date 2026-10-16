---
id: FATANALYSIS-18
title: Remove CSV import and implement initial bulk fetch for INIT Auth AFAT data
status: Done
assignee:
  - Remove CSV upload form
  - CSV parser endpoints and CSV tab from sync_management UI
  - >-
    Implement bulk crawler in AfatScraperService to discover and fetch all
    historical reports
  - Add one-click Initial Bulk Ingest button in sync management UI
  - All tests and linters pass
created_date: '2026-10-16 14:17'
updated_date: '2026-10-16 15:58'
labels: []
dependencies: []
ordinal: 18000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Remove obsolete CSV upload/paste functionality and implement a one-click bulk ingestion feature to crawl and fetch all historical AFAT reports directly from INIT Auth
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Removed obsolete CSV import functionality, enhanced HTML parser to extract corp-main-characters and character IDs from INIT Auth, implemented one-click initial bulk sync and single-month sync in UI, and added fatanalysis_sync_all management command.
<!-- SECTION:FINAL_SUMMARY:END -->
