---
id: FATANALYSIS-9
title: Configure automatic release and PyPI publishing
status: Done
assignee: []
created_date: '2026-08-25 21:07'
updated_date: '2026-08-25 21:10'
labels: []
dependencies: []
ordinal: 9000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Configure GitHub Actions and Commitizen to automatically publish releases to PyPI, similar to the setup in aa-industry.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 1. GitHub Action release.yml is added\n2. pyproject.toml includes commitizen configuration
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Created .github/workflows/release.yml and added tool.commitizen configuration to pyproject.toml
<!-- SECTION:NOTES:END -->
