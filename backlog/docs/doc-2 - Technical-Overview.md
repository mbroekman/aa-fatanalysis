---
id: doc-2
title: Technical Overview
type: guide
created_date: '2026-08-26 18:26'
---

# Technical Overview

This document tracks important architectural and technical decisions made during the development of `aa-fatanalysis`.

## 1. Permissions (General Model)
Alliance Auth requires permissions to be linked to a model to be assignable in the Django Admin. To handle the abstract `fatanalysis.basic_access` permission, a `General` model was introduced in `models.py` with `managed = False` and `default_permissions = ()`. This registers the custom permission natively without creating unneeded database tables.

## 2. Frontend / UI Framework
The application uses **Bootstrap 5**, aligning with the frontend framework adopted by Alliance Auth >= v4.0.0.
- Layouts, tabs, and modals use `data-bs-*` attributes.
- Charts are rendered dynamically using **Chart.js**.

## 3. CI/CD & Releases
Releases are handled automatically using **Commitizen** (`cz bump`) and **GitHub Actions**.
- `pyproject.toml` manages versioning centrally.
- PyPI publishing relies on **Trusted Publishing** (OIDC claims) mapped directly to the GitHub repository.
