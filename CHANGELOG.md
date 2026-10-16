## [Unreleased]

### Feat

- Redesign aa-fatanalysis for multi-year AFAT ingestion and dynamic time windows (FATANALYSIS-16)
- Introduce `FatMonthPeriod` and dynamic JSON `FatEntry` models replacing legacy fixed 30/90-day tables
- Implement `AfatScraperService` for remote AFAT ingestion via session cookie authentication
- Add director frontend management UI (`/fatanalysis/sync/`) with live credential testing, report URL ingestion, and direct CSV import
- Support dynamic dashboard aggregation across 30d, 90d, 120d, YTD, multi-year, and all-time windows
- Add longitudinal player FAT detail page with trend charts and participation breakdown
- Upgrade templates to strict Bootstrap 5 with AA top header version branding

## v0.2.0 (2026-08-26)

### Feat

- move overview buttons into tabs
- split trend chart into 30 and 90 day tabs

### Fix

- update tabs to Bootstrap 5 syntax

## v0.1.1 (2026-08-26)

### Fix

- add basic_access permission via General model

## v0.1.0 (2026-08-25)

### Feat

- add GitHub Actions workflow for automated PyPI releases and configure commitizen in pyproject.toml
- Initial commit for aa-fatanalysis plugin
