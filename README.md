# FAT Analysis

[![PyPI version](https://img.shields.io/pypi/v/aa-fatanalysis)](https://pypi.org/project/aa-fatanalysis/)
[![Python versions](https://img.shields.io/pypi/pyversions/aa-fatanalysis)](https://pypi.org/project/aa-fatanalysis/)
[![Tests](https://github.com/mbroekman/aa-fatanalysis/actions/workflows/automated-checks.yml/badge.svg)](https://github.com/mbroekman/aa-fatanalysis/actions/workflows/automated-checks.yml)

Alliance Auth plugin for analyzing FATs (Fleet Activity Tracking). This plugin provides multi-year AFAT ingestion, automated scraping from external Alliance Auth instances (e.g. INIT Auth) via session cookie authentication, direct CSV imports, and interactive dynamic dashboard visualizations (30d, 90d, 120d, YTD, multi-year) on both a per-character and per-corporation basis.

## Features

- **Multi-Year AFAT Ingestion**: Store and track monthly FAT periods across multiple years with dynamic fleet activity categorizations (e.g., Strategic, QRF, Peacetime).
- **INIT Auth Scraper**: Built-in scraper service to ingest reports directly from remote Alliance Auth AFAT instances using session cookies.
- **Frontend Director UI**: Manage scraper credentials, test live connections, trigger on-demand imports, and upload CSVs directly from the web interface without needing Django admin.
- **Dynamic Time Windows**: Switch instantly between 30 Days (Latest), 90 Days, 120 Days, YTD, specific years, and All Time.
- **Pilot Longitudinal Detail**: Track individual pilot participation trends over time with interactive Chart.js line and doughnut charts.
- **Permissions Management**: Separate `fatanalysis.basic_access` (members) and `fatanalysis.manage_fatanalysis` (directors/leadership).

## Installation

1. **Activate your Alliance Auth virtual environment**
   ```bash
   source /home/allianceserver/venv/auth/bin/activate
   ```

2. **Install the plugin**
   Navigate to the directory containing this plugin and run:
   ```bash
   pip install -e .
   ```
   *(Or install via git / pip once published to a repository)*

3. **Update your Alliance Auth settings**
   Add `'fatanalysis'` to your `INSTALLED_APPS` in `myauth/myauth/settings/local.py`:
   ```python
   INSTALLED_APPS += [
       "fatanalysis",
   ]
   ```

4. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Restart Alliance Auth services**
   ```bash
   sudo systemctl restart supervisor
   ```
   *(Or restart gunicorn and celery according to your specific setup)*

## Permissions
- `fatanalysis.basic_access`: Allows members to view the FAT Analysis dashboard, filter by time windows, and view player details.
- `fatanalysis.manage_fatanalysis`: Allows directors/leadership to access Sync & Ingestion management, configure the AFAT scraper, import CSVs, and manage/delete recording periods.
