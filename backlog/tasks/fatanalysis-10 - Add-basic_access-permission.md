---
id: FATANALYSIS-10
title: Add basic_access permission
status: Done
assignee: []
created_date: '2026-08-25 22:22'
updated_date: '2026-08-25 22:23'
labels: []
dependencies: []
ordinal: 10000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The app lacks a basic_access permission, making it only visible to superusers/admins. Add a basic_access permission to models.py and enforce it in auth_hooks.py and views.py.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 1. basic_access permission exists\n2. auth_hooks.py checks for basic_access\n3. views require basic_access
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Added General model to models.py containing basic_access permission. Generated migration 0003_general.py.
<!-- SECTION:NOTES:END -->
