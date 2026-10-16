---
id: FATANALYSIS-20
title: Fix duplicate year filter tabs in dashboard navigation
status: Done
assignee: []
created_date: '2026-10-16 16:49'
updated_date: '2026-10-16 16:51'
labels: []
dependencies: []
priority: high
type: bug
ordinal: 20000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Fix query in views.py where FatMonthPeriod.objects.values_list('year', flat=True).distinct() included 'month' due to Meta ordering, causing duplicate year buttons in index.html navigation.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Each distinct year in FatMonthPeriod appears exactly once in dashboard navigation buttons
- [ ] #2 Tests pass cleanly and regression test is added for available_years deduplication
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Resolved duplicate year buttons in dashboard filter bar by clearing default model ordering (.order_by()) and using set() deduplication in available_years query. Added regression unit test in test_views.py.
<!-- SECTION:FINAL_SUMMARY:END -->
