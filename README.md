# FAT Analysis

[![PyPI version](https://img.shields.io/pypi/v/aa-fatanalysis)](https://pypi.org/project/aa-fatanalysis/)
[![Python versions](https://img.shields.io/pypi/pyversions/aa-fatanalysis)](https://pypi.org/project/aa-fatanalysis/)
[![Tests](https://github.com/mbroekman/aa-fatanalysis/actions/workflows/automated-checks.yml/badge.svg)](https://github.com/mbroekman/aa-fatanalysis/actions/workflows/automated-checks.yml)

Alliance Auth plugin for analyzing FATs (Fleet Activity Tracking). This plugin allows for the upload of 30-day and 90-day FAT CSV files, parses them dynamically, and provides overviews and interactive charts on both a per-character and per-corporation basis.

## Features

- **CSV Import**: Upload standard FAT CSV files for both 30-day and 90-day periods.
- **Tabbed Dashboard**: A clean, modern Bootstrap 5 UI that separates 30-day and 90-day overview charts into easy-to-use tabs.
- **Interactive Charts**: Powered by Chart.js for tracking FAT trends over time on both Alliance and Player levels.
- **Permissions Management**: Easily restrict access to the dashboard using the built-in `fatanalysis.basic_access` permission.

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
       'fatanalysis',
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
Assign the `fatanalysis.basic_access` permission in the admin panel to any user or group that should have access to view and upload FAT analysis data.
